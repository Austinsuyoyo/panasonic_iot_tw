"""Unit tests for the washer detergent-low flag decoded from register 0x71.

Bit 8 (0x0100) was set through three separate low-detergent events, in both
idle and running states, and cleared as soon as the tank was refilled - the
refilled reading was taken at the same cycle stage (0x34=16) that had
previously reported the bit set, so the value does not merely follow the
programme.
"""
import pytest
from unittest.mock import Mock

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.panasonic_iot_tw.devices.washing_machine import WashingMachineDevice

DEVICE_DATA = {
    "device_id": "washer1",
    "nickname": "Test Washer",
    "model": "NA-VS120RW",
    "version": "1.0.0",
    "available": True,
}


def _sensors(status):
    coordinator = Mock()
    coordinator.last_update_success = True
    coordinator.data = {"washer1": {**DEVICE_DATA, "status": status}}
    device = WashingMachineDevice(coordinator, "washer1", DEVICE_DATA)
    return {
        e._attr_unique_id.split("washer1_", 1)[1]: e
        for e in device.get_binary_sensor_entities(coordinator)
    }


class TestDetergentLow:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            (256, True),    # 0x0100 - observed on every low-detergent event
            (0, False),     # observed right after refilling
            (512, False),   # a different bit alone must not trigger
            (768, True),    # 0x0300 - bit 8 set alongside another bit
        ],
    )
    def test_bit8_decodes_detergent(self, raw, expected):
        sensors = _sensors({"0x71": raw, "0x50": 2})
        assert sensors["detergent_low"].is_on is expected

    def test_is_a_problem_not_a_running_state(self):
        sensors = _sensors({"0x71": 0, "0x50": 0})
        assert sensors["detergent_low"].device_class is BinarySensorDeviceClass.PROBLEM

    def test_independent_of_operation_status(self):
        """The flag held across idle and running alike, so 0x50 must not gate it."""
        for operation_status in (0, 1, 2, 5):
            sensors = _sensors({"0x71": 256, "0x50": operation_status})
            assert sensors["detergent_low"].is_on is True

    def test_missing_register_is_none(self):
        sensors = _sensors({"0x50": 2})
        assert sensors["detergent_low"].is_on is None

    def test_not_read_from_the_state_tracking_register(self):
        """0x5A follows the operation status, not the tank - it must be ignored."""
        sensors = _sensors({"0x5A": 2, "0x71": 0, "0x50": 0})
        assert sensors["detergent_low"].is_on is False
