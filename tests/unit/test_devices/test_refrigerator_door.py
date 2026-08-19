"""Unit tests for the fridge door-ajar alarm decoded from register 0x66.

Bit 15 is not the live door state: the appliance raises it only after a
door has stayed open past its own alarm delay (owner-observed 2026-08-19).
"""
import pytest
from unittest.mock import Mock

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.panasonic_iot_tw.devices.refrigerator import RefrigeratorDevice

DEVICE_DATA = {
    "device_id": "fridge1",
    "nickname": "Test Fridge",
    "model": "NR-D611XGS",
    "version": "1.0.0",
    "available": True,
}


def _sensors(status):
    coordinator = Mock()
    coordinator.last_update_success = True
    coordinator.data = {"fridge1": {**DEVICE_DATA, "status": status}}
    device = RefrigeratorDevice(coordinator, "fridge1", DEVICE_DATA)
    return coordinator, {
        e._attr_unique_id.split("fridge1_", 1)[1]: e
        for e in device.get_binary_sensor_entities(coordinator)
    }


class TestRefrigeratorDoorAlarm:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            (552, False),      # 0x0228 — no alarm
            (33320, True),     # 0x8228 — bit 15 set: door open past the alarm delay
            (696, False),      # 0x02B8 — a different low-byte value, still no alarm
            (0x8000, True),    # bit 15 alone
            (0, False),
        ],
    )
    def test_alarm_bit(self, raw, expected):
        coordinator, sensors = _sensors({"0x66": raw})
        assert sensors["door"].is_on is expected

    def test_device_class(self):
        _, sensors = _sensors({"0x66": 552})
        # PROBLEM, not DOOR: the bit is the appliance's door-ajar alarm,
        # not the physical door position.
        assert sensors["door"].device_class is BinarySensorDeviceClass.PROBLEM

    def test_missing_register(self):
        _, sensors = _sensors({})
        assert sensors["door"].is_on is None
