"""Unit tests for live (non-stale) entity availability and device_id keying."""
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.panasonic_iot_tw.switch import PanasonicSwitch


DEVICE_KEY = "device-abc"


def _make_coordinator(available=True, status=None):
    coordinator = Mock()
    coordinator.last_update_success = True
    coordinator.data = {
        DEVICE_KEY: {
            "device_id": DEVICE_KEY,
            "nickname": "Test Switch",
            "model": "X",
            "available": available,
            "status": status if status is not None else {"0x00": 1},
        }
    }
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def _make_switch(coordinator):
    device_data = {
        "device_id": DEVICE_KEY,
        "nickname": "Test Switch",
        "model": "X",
        "available": True,  # setup-time snapshot says available
    }
    return PanasonicSwitch(
        coordinator, DEVICE_KEY, device_data, "0x00", "Power", "power"
    )


def test_unique_id_format_unchanged():
    """unique_id must remain f'{device_id}_{entity_key}'."""
    switch = _make_switch(_make_coordinator())
    assert switch.unique_id == f"{DEVICE_KEY}_power"


def test_availability_reads_live_data():
    """Entity reflects the live coordinator value, not the setup snapshot."""
    coordinator = _make_coordinator(available=True)
    switch = _make_switch(coordinator)
    assert switch.available is True

    # Device becomes unavailable in the coordinator (snapshot still says True)
    coordinator.data[DEVICE_KEY]["available"] = False
    assert switch.available is False


def test_status_read_by_device_id():
    """Status lookups resolve through the device_id key."""
    coordinator = _make_coordinator(status={"0x00": 1})
    switch = _make_switch(coordinator)
    assert switch.is_on is True

    coordinator.data[DEVICE_KEY]["status"]["0x00"] = 0
    assert switch.is_on is False


async def test_send_command_uses_device_id_key():
    """Commands are dispatched with the device_id key."""
    coordinator = _make_coordinator()
    coordinator.smart_app = AsyncMock()
    coordinator.smart_app.set_device_command.return_value = True
    switch = _make_switch(coordinator)

    await switch.async_turn_on()

    coordinator.smart_app.set_device_command.assert_awaited_once()
    args = coordinator.smart_app.set_device_command.await_args.args
    assert args[0] == DEVICE_KEY
    coordinator.async_request_refresh.assert_awaited_once()


async def test_send_command_failure_raises():
    """A rejected command raises HomeAssistantError to surface in the UI."""
    coordinator = _make_coordinator()
    coordinator.smart_app = AsyncMock()
    coordinator.smart_app.set_device_command.return_value = False
    switch = _make_switch(coordinator)

    with pytest.raises(HomeAssistantError):
        await switch.async_turn_on()
