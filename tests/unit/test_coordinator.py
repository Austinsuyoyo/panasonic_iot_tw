"""Unit tests for the PanasonicCoordinator."""
from datetime import datetime

import pytest
from unittest.mock import AsyncMock

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.panasonic_iot_tw.const import (
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)
from custom_components.panasonic_iot_tw.coordinator import PanasonicCoordinator
from custom_components.panasonic_iot_tw.exceptions import (
    PanasonicLoginFailed,
    PanasonicTokenExpired,
)


def _make_entry(hass, options=None):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "user@example.com", "password": "secret"},
        options=options or {CONF_UPDATE_INTERVAL: 120},
        version=2,
    )
    entry.add_to_hass(hass)
    return entry


async def test_update_interval_from_options(hass):
    """Coordinator reads its update interval from entry options."""
    entry = _make_entry(hass, options={CONF_UPDATE_INTERVAL: 300})
    smart_app = AsyncMock()
    coordinator = PanasonicCoordinator(hass, entry, smart_app)

    assert coordinator.update_interval.total_seconds() == 300
    assert coordinator.smart_app is smart_app


async def test_update_success(hass):
    """Coordinator returns device data keyed by device_id on success."""
    entry = _make_entry(hass)
    smart_app = AsyncMock()
    smart_app.get_device_with_info.return_value = {
        "dev-1": {"device_id": "dev-1", "available": True, "status": {}},
    }
    coordinator = PanasonicCoordinator(hass, entry, smart_app)

    data = await coordinator._async_update_data()

    assert "dev-1" in data


def _freeze(monkeypatch, when):
    import custom_components.panasonic_iot_tw.coordinator as coord_mod

    class _FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return when

    monkeypatch.setattr(coord_mod, "datetime", _FakeDatetime)


@pytest.mark.parametrize("exc", [PanasonicLoginFailed, PanasonicTokenExpired])
async def test_single_auth_error_retries_as_update_failed(hass, exc, monkeypatch):
    """A first auth failure is retried, never instantly escalated to reauth."""
    _freeze(monkeypatch, datetime(2026, 7, 17, 12, 0, 0))
    entry = _make_entry(hass)
    smart_app = AsyncMock()
    smart_app.get_device_with_info.side_effect = exc("boom")
    coordinator = PanasonicCoordinator(hass, entry, smart_app)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_persistent_auth_error_raises_auth_failed(hass, monkeypatch):
    """Auth failing 3+ times over 30+ minutes in the daytime triggers reauth."""
    entry = _make_entry(hass)
    smart_app = AsyncMock()
    smart_app.get_device_with_info.side_effect = PanasonicLoginFailed("boom")
    coordinator = PanasonicCoordinator(hass, entry, smart_app)

    for minute in (0, 15):
        _freeze(monkeypatch, datetime(2026, 7, 17, 12, minute, 0))
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    _freeze(monkeypatch, datetime(2026, 7, 17, 12, 31, 0))
    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_auth_error_never_escalates_in_maintenance_window(hass, monkeypatch):
    """Persistent auth failures during 00:00-08:00 keep retrying."""
    entry = _make_entry(hass)
    smart_app = AsyncMock()
    smart_app.get_device_with_info.side_effect = PanasonicLoginFailed("boom")
    coordinator = PanasonicCoordinator(hass, entry, smart_app)

    for minute in (0, 15, 31, 45):
        _freeze(monkeypatch, datetime(2026, 7, 17, 0, minute, 0))
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


async def test_success_resets_auth_failure_tracking(hass, monkeypatch):
    """A successful update clears the auth failure counters."""
    entry = _make_entry(hass)
    smart_app = AsyncMock()
    coordinator = PanasonicCoordinator(hass, entry, smart_app)

    for minute in (0, 15):
        _freeze(monkeypatch, datetime(2026, 7, 17, 12, minute, 0))
        smart_app.get_device_with_info.side_effect = PanasonicLoginFailed("boom")
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    smart_app.get_device_with_info.side_effect = None
    smart_app.get_device_with_info.return_value = {"dev-1": {"available": True}}
    _freeze(monkeypatch, datetime(2026, 7, 17, 12, 20, 0))
    await coordinator._async_update_data()

    _freeze(monkeypatch, datetime(2026, 7, 17, 12, 40, 0))
    smart_app.get_device_with_info.side_effect = PanasonicLoginFailed("boom")
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_other_error_raises_update_failed(hass):
    """Generic communication failures map to UpdateFailed."""
    entry = _make_entry(hass)
    smart_app = AsyncMock()
    smart_app.get_device_with_info.side_effect = RuntimeError("network down")
    coordinator = PanasonicCoordinator(hass, entry, smart_app)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
