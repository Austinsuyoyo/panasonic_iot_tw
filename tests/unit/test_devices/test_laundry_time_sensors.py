"""Unit tests for washer/dryer duration sensor gating."""
import pytest
from unittest.mock import Mock

from homeassistant.helpers.entity import EntityCategory

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


class TestErrorCodeSensor:
    """The error register is decoded into the code shown on the machine."""

    # The two machines report the panel code in different registers:
    # verified live, the washer uses 0x19 and the dryer 0x0A.
    @pytest.mark.parametrize(
        "device_cls,status,register",
        [
            (WashingMachineDevice, WASHER_STATUS, "0x19"),
            (DryerDevice, DRYER_STATUS, "0x0A"),
        ],
    )
    @pytest.mark.parametrize(
        "raw,expected",
        [
            (0, None),          # no fault
            (21771, "U11"),     # 0x550B — drain fault
            (21772, "U12"),     # 0x550C — lid not closed
            (0x4801, "H01"),
            (12345, "0x3039"),  # unknown layout falls back to raw hex
        ],
    )
    def test_decodes_panel_code(self, device_cls, status, register, raw, expected):
        coordinator, sensors = _sensors(device_cls, status)
        _set_status(coordinator, **{register: raw, "0x50": 2})
        assert sensors["error_code"].native_value == expected

    def test_dryer_ignores_the_washer_register(self):
        """0x19 reads 0 on the dryer even during a fault, so it must not be used."""
        coordinator, sensors = _sensors(DryerDevice, DRYER_STATUS)
        _set_status(coordinator, **{"0x19": 21772, "0x0A": 0, "0x50": 8})
        assert sensors["error_code"].native_value is None

    def test_raw_value_kept_as_attribute(self):
        coordinator, sensors = _sensors(WashingMachineDevice, WASHER_STATUS)
        _set_status(coordinator, **{"0x19": 21771, "0x50": 8})
        assert sensors["error_code"].extra_state_attributes == {"raw_value": 21771}

    def test_missing_register_is_none(self):
        coordinator, sensors = _sensors(WashingMachineDevice, WASHER_STATUS)
        _set_status(coordinator, **{"0x50": 2})
        assert sensors["error_code"].native_value is None

    def test_is_diagnostic(self):
        _, sensors = _sensors(WashingMachineDevice, WASHER_STATUS)
        assert sensors["error_code"].entity_category is EntityCategory.DIAGNOSTIC
