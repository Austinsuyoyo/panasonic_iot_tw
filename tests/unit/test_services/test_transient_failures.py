"""Short cloud failures must not blank entities or hide their cause."""
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.panasonic_iot_tw.base import value_processors
from custom_components.panasonic_iot_tw.const import TRANSIENT_FAILURE_TOLERANCE
from custom_components.panasonic_iot_tw.exceptions import PanasonicDeviceOffline
from custom_components.panasonic_iot_tw.services.device_service import DeviceService
from custom_components.panasonic_iot_tw.services.smart_app import SmartApp


def _poll(app, available):
    data = {"fridge": {"device_id": "fridge", "available": available,
                       "status": {"0x00": "1"} if available else {}}}
    app._bridge_transient_device_failures(data)
    app._devices_cache = data
    return data["fridge"]


def test_device_failure_keeps_last_state_then_goes_unavailable():
    app = SmartApp(Mock(), "user", "pw")
    assert _poll(app, True)["available"]
    for _ in range(TRANSIENT_FAILURE_TOLERANCE):
        bridged = _poll(app, False)
        assert bridged["available"] and bridged["status"] == {"0x00": "1"}
    assert not _poll(app, False)["available"]
    assert _poll(app, True)["available"]


def test_never_seen_device_is_not_bridged():
    app = SmartApp(Mock(), "user", "pw")
    assert not _poll(app, False)["available"]


async def test_device_list_failure_propagates():
    """A DNS timeout on the device list used to look like a poll with 0 devices."""
    api_client = Mock()
    api_client.request = AsyncMock(side_effect=PanasonicDeviceOffline("DNS timeout"))
    token_manager = Mock()
    token_manager.ensure_authenticated = AsyncMock()
    with pytest.raises(PanasonicDeviceOffline):
        await DeviceService(api_client, token_manager).get_device_list()


def test_no_data_marker_is_not_a_reading():
    assert value_processors.raw_register_word("30") == 30
    with pytest.raises(ValueError):
        value_processors.raw_register_word("65535")
    with pytest.raises(ValueError):
        value_processors.process_status_flag_bits("65535")
