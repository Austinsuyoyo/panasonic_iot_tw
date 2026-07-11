"""Unit tests for the PanasonicCoordinator."""
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


@pytest.mark.parametrize("exc", [PanasonicLoginFailed, PanasonicTokenExpired])
async def test_auth_error_raises_config_entry_auth_failed(hass, exc):
    """Auth failures map to ConfigEntryAuthFailed."""
    entry = _make_entry(hass)
    smart_app = AsyncMock()
    smart_app.get_device_with_info.side_effect = exc("boom")
    coordinator = PanasonicCoordinator(hass, entry, smart_app)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator._async_update_data()


async def test_other_error_raises_update_failed(hass):
    """Generic communication failures map to UpdateFailed."""
    entry = _make_entry(hass)
    smart_app = AsyncMock()
    smart_app.get_device_with_info.side_effect = RuntimeError("network down")
    coordinator = PanasonicCoordinator(hass, entry, smart_app)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
