"""Unit tests for washer/dryer duration sensor gating."""
import pytest
from unittest.mock import Mock

from custom_components.panasonic_iot_tw.devices.dryer import DryerDevice
from custom_components.panasonic_iot_tw.devices.washing_machine import WashingMachineDevice

def _coordinator(status):
    coordinator = Mock()
    coordinator.last_update_success = True
    coordinator.data = {
        "dev1": {
            "device_id": "dev1",
            "nickname": "Test Laundry",
            "model": "Test Model",
            "version": "1.0.0",
            "available": True,
            "status": status,
        }
    }
    return coordinator


DEVICE_DATA = {
    "device_id": "dev1",
    "nickname": "Test Laundry",
    "model": "Test Model",
    "version": "1.0.0",
    "available": True,
}


def _sensors(device_cls, status):
    """Build the sensor entities for a device against the given raw status."""
    coordinator = _coordinator(status)
    device = device_cls(coordinator, "dev1", DEVICE_DATA)
    return coordinator, {
        entity._attr_unique_id.split("dev1_", 1)[1]: entity
        for entity in device.get_sensor_entities(coordinator)
    }


def _set_status(coordinator, **status):
    coordinator.data["dev1"]["status"] = status


WASHER_STATUS = {"0x13": 47, "0x15": 3, "0x50": 2, "0x55": 1}
DRYER_STATUS = {"0x05": 47, "0x15": 3, "0x50": 2, "0x55": 1}


class TestDurationSensorGating:
    """Duration sensors keep DURATION but drop state_class and follow 0x50."""

    @pytest.mark.parametrize(
        "device_cls,status,remaining_key,remaining_cmd",
        [
            (WashingMachineDevice, WASHER_STATUS, "washing_remaining_time", "0x13"),
            (DryerDevice, DRYER_STATUS, "drying_remaining_time", "0x05"),
        ],
    )
    def test_no_state_class(self, device_cls, status, remaining_key, remaining_cmd):
        _, sensors = _sensors(device_cls, status)
        assert sensors[remaining_key].state_class is None
        assert sensors["schedule_remaining_time"].state_class is None

    @pytest.mark.parametrize(
        "device_cls,status,remaining_key,remaining_cmd",
        [
            (WashingMachineDevice, WASHER_STATUS, "washing_remaining_time", "0x13"),
            (DryerDevice, DRYER_STATUS, "drying_remaining_time", "0x05"),
        ],
    )
    @pytest.mark.parametrize(
        "operation_status,expected",
        [(0, None), (1, 47), (2, 47), (3, 47), (4, 47), (5, None), (8, None)],
    )
    def test_remaining_time_gate(
        self, device_cls, status, remaining_key, remaining_cmd,
        operation_status, expected
    ):
        coordinator, sensors = _sensors(device_cls, status)
        _set_status(coordinator, **{remaining_cmd: 47, "0x50": operation_status})
        assert sensors[remaining_key].native_value == expected

    @pytest.mark.parametrize(
        "device_cls,status",
        [(WashingMachineDevice, WASHER_STATUS), (DryerDevice, DRYER_STATUS)],
    )
    @pytest.mark.parametrize(
        "operation_status,expected",
        [(0, None), (1, None), (2, None), (3, 3), (4, 3), (5, None)],
    )
    def test_schedule_remaining_time_gate(
        self, device_cls, status, operation_status, expected
    ):
        coordinator, sensors = _sensors(device_cls, status)
        _set_status(coordinator, **{"0x15": 3, "0x50": operation_status})
        assert sensors["schedule_remaining_time"].native_value == expected

    def test_missing_gate_status_returns_none(self):
        coordinator, sensors = _sensors(WashingMachineDevice, WASHER_STATUS)
        _set_status(coordinator, **{"0x13": 47})
        assert sensors["washing_remaining_time"].native_value is None
        assert sensors["washing_remaining_time"].extra_state_attributes is None

