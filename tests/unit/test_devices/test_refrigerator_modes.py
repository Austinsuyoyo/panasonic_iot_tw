"""Unit tests for the fridge mode enum sensors (0x56/0x5A/0x5B/0x5C)."""
import pytest
from unittest.mock import Mock

from homeassistant.components.sensor import SensorDeviceClass

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
    return {
        e._attr_unique_id.split("fridge1_", 1)[1]: e
        for e in device.get_sensor_entities(coordinator)
    }


class TestRefrigeratorModeSensors:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            (0, "normal"),
            (1, "cooling"),
            (2, "quick_cool"),
            (3, "quick_freeze"),
            (4, None),
        ],
    )
    def test_fresh_freezing_mode(self, raw, expected):
        sensors = _sensors({"0x56": raw})
        assert sensors["fresh_freezing_mode"].native_value == expected

    @pytest.mark.parametrize("key,register", [
        ("winter_mode", "0x5A"),
        ("shopping_mode", "0x5B"),
        ("vacation_mode", "0x5C"),
    ])
    @pytest.mark.parametrize("raw,expected", [
        (0, "inactive"),
        (1, "active"),
        (2, "available"),
        (3, None),
    ])
    def test_activation_modes(self, key, register, raw, expected):
        sensors = _sensors({register: raw})
        assert sensors[key].native_value == expected

    @pytest.mark.parametrize("key,options", [
        ("fresh_freezing_mode", ["normal", "cooling", "quick_cool", "quick_freeze"]),
        ("winter_mode", ["inactive", "active", "available"]),
        ("shopping_mode", ["inactive", "active", "available"]),
        ("vacation_mode", ["inactive", "active", "available"]),
    ])
    def test_enum_declaration(self, key, options):
        sensors = _sensors({"0x56": 0, "0x5A": 0, "0x5B": 0, "0x5C": 0})
        sensor = sensors[key]
        assert sensor.device_class is SensorDeviceClass.ENUM
        assert sensor.options == options
        # ENUM sensors must carry no unit and no state class
        assert sensor.native_unit_of_measurement is None
        assert sensor.state_class is None
