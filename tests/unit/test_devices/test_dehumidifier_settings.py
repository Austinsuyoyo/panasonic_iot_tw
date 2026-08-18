"""Unit tests for dehumidifier auxiliary settings (category and timer units)."""
import pytest
from unittest.mock import Mock

from homeassistant.components.number import NumberDeviceClass
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from custom_components.panasonic_iot_tw.devices.dehumidifier import DehumidifierDevice

DEVICE_DATA = {
    "device_id": "dehum1",
    "nickname": "Test Dehumidifier",
    "model": "Test Dehumidifier Model",
    "version": "1.0.0",
    "available": True,
}


@pytest.fixture
def device():
    coordinator = Mock()
    coordinator.last_update_success = True
    coordinator.data = {"dehum1": {**DEVICE_DATA, "status": {}}}
    return DehumidifierDevice(coordinator, "dehum1", DEVICE_DATA), coordinator


class TestDehumidifierSettings:
    def test_buzzer_is_config(self, device):
        dehumidifier, coordinator = device
        switches = {
            s._attr_unique_id: s
            for s in dehumidifier.get_switch_entities(coordinator)
        }
        assert switches["dehum1_buzzer"].entity_category is EntityCategory.CONFIG
        assert switches["dehum1_nanoe"].entity_category is None

    def test_timer_numbers(self, device):
        dehumidifier, coordinator = device
        numbers = {
            n._attr_unique_id: n
            for n in dehumidifier.get_number_entities(coordinator)
        }
        for key in ("on_timer", "off_timer"):
            number = numbers[f"dehum1_{key}"]
            assert number.native_unit_of_measurement == UnitOfTime.HOURS
            assert number.device_class is NumberDeviceClass.DURATION
            assert number.entity_category is EntityCategory.CONFIG

        # Target humidity is a primary control, not a setting
        assert numbers["dehum1_target_humidity"].entity_category is None
