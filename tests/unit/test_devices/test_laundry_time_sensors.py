"""Unit tests for washer/dryer duration gating and timestamp sensors."""
from datetime import datetime, timedelta, timezone

import pytest
from unittest.mock import Mock

from custom_components.panasonic_iot_tw import sensor as sensor_module
from custom_components.panasonic_iot_tw.devices.dryer import DryerDevice
from custom_components.panasonic_iot_tw.devices.washing_machine import WashingMachineDevice

BASE_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def frozen_now(monkeypatch):
    """Freeze dt_util.utcnow() and allow the test to advance it."""
    holder = {"now": BASE_NOW}
    monkeypatch.setattr(sensor_module.dt_util, "utcnow", lambda: holder["now"])
    return holder


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


class TestFinishTime:
    """finish_time reports now + remaining minutes while running."""

    @pytest.mark.parametrize(
        "device_cls,status,remaining_cmd",
        [
            (WashingMachineDevice, WASHER_STATUS, "0x13"),
            (DryerDevice, DRYER_STATUS, "0x05"),
        ],
    )
    def test_running_returns_timestamp(
        self, device_cls, status, remaining_cmd, frozen_now
    ):
        coordinator, sensors = _sensors(device_cls, status)
        _set_status(coordinator, **{remaining_cmd: 47, "0x50": 2})

        value = sensors["finish_time"].native_value
        assert value == BASE_NOW + timedelta(minutes=47)
        assert value.tzinfo is not None

    @pytest.mark.parametrize("operation_status", [0, 1, 3, 4, 5, 8])
    def test_not_running_returns_none(self, operation_status, frozen_now):
        coordinator, sensors = _sensors(WashingMachineDevice, WASHER_STATUS)
        _set_status(coordinator, **{"0x13": 47, "0x50": operation_status})
        assert sensors["finish_time"].native_value is None

    def test_unique_ids(self):
        _, sensors = _sensors(WashingMachineDevice, WASHER_STATUS)
        assert sensors["finish_time"]._attr_unique_id == "dev1_finish_time"
        assert (
            sensors["scheduled_start_time"]._attr_unique_id
            == "dev1_scheduled_start_time"
        )


class TestJitterClamp:
    """Small poll-to-poll drift must not move the emitted timestamp."""

    def test_small_drift_keeps_timestamp(self, frozen_now):
        coordinator, sensors = _sensors(WashingMachineDevice, WASHER_STATUS)
        _set_status(coordinator, **{"0x13": 47, "0x50": 2})
        first = sensors["finish_time"].native_value

        frozen_now["now"] = BASE_NOW + timedelta(minutes=1)
        _set_status(coordinator, **{"0x13": 48, "0x50": 2})
        assert sensors["finish_time"].native_value == first

    def test_large_drift_updates_timestamp(self, frozen_now):
        coordinator, sensors = _sensors(WashingMachineDevice, WASHER_STATUS)
        _set_status(coordinator, **{"0x13": 47, "0x50": 2})
        first = sensors["finish_time"].native_value

        _set_status(coordinator, **{"0x13": 52, "0x50": 2})
        second = sensors["finish_time"].native_value
        assert second == BASE_NOW + timedelta(minutes=52)
        assert second != first

    def test_gate_close_reseeds_clamp(self, frozen_now):
        coordinator, sensors = _sensors(WashingMachineDevice, WASHER_STATUS)
        _set_status(coordinator, **{"0x13": 47, "0x50": 2})
        sensors["finish_time"].native_value

        _set_status(coordinator, **{"0x13": 47, "0x50": 5})
        assert sensors["finish_time"].native_value is None

        frozen_now["now"] = BASE_NOW + timedelta(hours=2)
        _set_status(coordinator, **{"0x13": 48, "0x50": 2})
        assert sensors["finish_time"].native_value == frozen_now["now"] + timedelta(
            minutes=48
        )

    def test_scheduled_start_time_clamp(self, frozen_now):
        coordinator, sensors = _sensors(DryerDevice, DRYER_STATUS)
        _set_status(coordinator, **{"0x15": 3, "0x50": 3})
        first = sensors["scheduled_start_time"].native_value
        assert first == BASE_NOW + timedelta(hours=3)

        # 30 minutes of drift is within the hour-granularity tolerance
        frozen_now["now"] = BASE_NOW + timedelta(minutes=30)
        assert sensors["scheduled_start_time"].native_value == first

        # A whole hour of drift moves the timestamp
        _set_status(coordinator, **{"0x15": 4, "0x50": 3})
        assert sensors["scheduled_start_time"].native_value == frozen_now[
            "now"
        ] + timedelta(hours=4)


class TestScheduledStartTime:
    """scheduled_start_time only reports while a reservation is pending."""

    @pytest.mark.parametrize(
        "device_cls,status", [(WashingMachineDevice, WASHER_STATUS), (DryerDevice, DRYER_STATUS)]
    )
    @pytest.mark.parametrize("operation_status", [3, 4])
    def test_reserved_returns_timestamp(
        self, device_cls, status, operation_status, frozen_now
    ):
        coordinator, sensors = _sensors(device_cls, status)
        _set_status(coordinator, **{"0x15": 3, "0x50": operation_status})
        assert sensors["scheduled_start_time"].native_value == BASE_NOW + timedelta(
            hours=3
        )

    @pytest.mark.parametrize("operation_status", [0, 1, 2, 5, 8])
    def test_not_reserved_returns_none(self, operation_status, frozen_now):
        coordinator, sensors = _sensors(DryerDevice, DRYER_STATUS)
        _set_status(coordinator, **{"0x15": 3, "0x50": operation_status})
        assert sensors["scheduled_start_time"].native_value is None
