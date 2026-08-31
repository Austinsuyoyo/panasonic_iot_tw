"""Dryer device logic for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, List

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfTime

from ..base import BaseDevice, value_processors
from ..const import (
    DRYER_AVAILABLE_STATUS,
    DRYER_AVAILABLE_CYCLES
)

_LOGGER = logging.getLogger(__name__)


class DryerDevice(BaseDevice):
    """Dryer device logic."""

    # Device registers, ordered by command type. const.py's
    # DEVICE_STATUS_CODES decides which of them are polled.
    DRYING_REMAINING_TIME_COMMAND = "0x05"    # Drying remaining time (0-599 min)    Sensor

    # Not 0x19: during a deliberate U12 this register read 0x550C while
    # 0x19 stayed 0. The washer is the one that uses 0x19.
    ERROR_CODE_COMMAND = "0x0A"               # Panel error code, 0 = no fault       Sensor

    SCHEDULE_REMAINING_TIME_COMMAND = "0x15"  # Reservation remaining time (0-24 h)  Sensor
    ENGINEERING_INFO_COMMAND = "0x34"         # Stage bits 8/4/2                     3x BinarySensor

    # Also gates the remaining-time sensors: they report nothing while idle,
    # because the register keeps the last programme's duration.
    OPERATION_STATUS_COMMAND = "0x50"         # Operation status, 8 = fault          Sensor

    CYCLE_MESSAGE_COMMAND = "0x55"            # Selected programme                   Sensor
    REMOTE_CONTROL_COMMAND = "0x74"           # Remote control allowed               BinarySensor

    # Operation status (0x50) values for which a remaining time is meaningful
    RUNNING_STATUS = 2
    REMAINING_TIME_STATUSES = {1, 2, 3, 4}      # standby / running / reserved
    RESERVED_STATUSES = {3, 4}                  # reservation pending

    @property
    def device_data(self) -> Dict[str, Any]:
        """Return device data with dynamic availability based on operation status."""
        data = self._device_data.copy()

        # Check operation status (0x50) - if 0 (not displayed), make all sensors unavailable
        try:
            operation_status = self.get_int_status(self.OPERATION_STATUS_COMMAND, default=1)
            # When operation status is 0, sensors should be unavailable
            if operation_status == 0:
                data["available"] = False
                _LOGGER.debug("Dryer device %s sensors unavailable: operation status = 0", self.device_key)
            else:
                # Keep original availability status when operation status is not 0
                data["available"] = self._device_data.get("available", False)
        except Exception as e:
            _LOGGER.warning("Error checking dryer operation status: %s", e)
            # Fallback to original availability on error
            data["available"] = self._device_data.get("available", False)

        return data
    
    def get_sensor_entities(self, coordinator) -> List:
        """Return sensor entities for dryer."""
        return [
            # Time sensors with formatting
            self._create_sensor(
                coordinator,
                command_type=self.DRYING_REMAINING_TIME_COMMAND,
                name="乾衣殘時間",
                sensor_key="drying_remaining_time",
                device_class=SensorDeviceClass.DURATION,
                unit=UnitOfTime.MINUTES,
                value_processor=value_processors.safe_int,
                extra_state_processor=value_processors.create_time_formatter("minutes"),
                gate_command=self.OPERATION_STATUS_COMMAND,
                gate_allowed=self.REMAINING_TIME_STATUSES,
                translation_key="dryer_drying_remaining_time"
            ),
            self._create_sensor(
                coordinator,
                command_type=self.SCHEDULE_REMAINING_TIME_COMMAND,
                name="預約殘時間",
                sensor_key="schedule_remaining_time",
                device_class=SensorDeviceClass.DURATION,
                unit=UnitOfTime.HOURS,
                value_processor=value_processors.safe_int,
                extra_state_processor=value_processors.create_time_formatter("hours"),
                gate_command=self.OPERATION_STATUS_COMMAND,
                gate_allowed=self.RESERVED_STATUSES,
                translation_key="dryer_schedule_remaining_time"
            ),
            # Status sensors with mapping
            self._create_sensor(
                coordinator,
                command_type=self.OPERATION_STATUS_COMMAND,
                name="運轉情報",
                sensor_key="operation_status",
                device_class=SensorDeviceClass.ENUM,
                options=list(dict.fromkeys(DRYER_AVAILABLE_STATUS.values())),
                value_processor=value_processors.create_status_mapping_processor(DRYER_AVAILABLE_STATUS),
                translation_key="dryer_operation_status"
            ),
            self._create_sensor(
                coordinator,
                command_type=self.CYCLE_MESSAGE_COMMAND,
                name="行程別訊息",
                sensor_key="cycle_message",
                device_class=SensorDeviceClass.ENUM,
                options=list(dict.fromkeys(DRYER_AVAILABLE_CYCLES.values())),
                value_processor=value_processors.create_status_mapping_processor(DRYER_AVAILABLE_CYCLES),
                translation_key="dryer_cycle_message"
            ),
            # Undecoded registers kept for the "clean the filter" reminder,
            # which the vendor app raises but no decoded register reflects.
            # 0x75 read 1024 during one such alert and is the main suspect.
            self._create_sensor(
                coordinator,
                command_type="0x71",
                name="暫存器 0x71",
                sensor_key="register_71",
                value_processor=value_processors.safe_int,
                extra_state_processor=value_processors.process_status_flag_bits,
                entity_category=EntityCategory.DIAGNOSTIC,
                translation_key="dryer_register_71"
            ),
            self._create_sensor(
                coordinator,
                command_type="0x72",
                name="暫存器 0x72",
                sensor_key="register_72",
                value_processor=value_processors.safe_int,
                extra_state_processor=value_processors.process_status_flag_bits,
                entity_category=EntityCategory.DIAGNOSTIC,
                translation_key="dryer_register_72"
            ),
            self._create_sensor(
                coordinator,
                command_type="0x73",
                name="暫存器 0x73",
                sensor_key="register_73",
                value_processor=value_processors.safe_int,
                extra_state_processor=value_processors.process_status_flag_bits,
                entity_category=EntityCategory.DIAGNOSTIC,
                translation_key="dryer_register_73"
            ),
            self._create_sensor(
                coordinator,
                command_type="0x75",
                name="暫存器 0x75",
                sensor_key="register_75",
                value_processor=value_processors.safe_int,
                extra_state_processor=value_processors.process_status_flag_bits,
                entity_category=EntityCategory.DIAGNOSTIC,
                translation_key="dryer_register_75"
            ),
            self._create_sensor(
                coordinator,
                command_type=self.ERROR_CODE_COMMAND,
                name="錯誤代碼",
                sensor_key="error_code",
                value_processor=value_processors.process_error_code,
                extra_state_processor=value_processors.process_error_code_attributes,
                entity_category=EntityCategory.DIAGNOSTIC,
                translation_key="dryer_error_code"
            ),
        ]
    
    def get_binary_sensor_entities(self, coordinator) -> List:
        """Return binary sensor entities for dryer."""
        return [
            # Engineering info 0x34 - 3 bitwise sensors
            self._create_binary_sensor(
                coordinator,
                command_type=self.ENGINEERING_INFO_COMMAND,
                name="工程資訊 - 乾衣(bit 1)",
                sensor_key="drying_status",
                device_class=BinarySensorDeviceClass.RUNNING,
                bit_mask=8,
                translation_key="dryer_drying_status",
                entity_registry_enabled_default=False
            ),
            self._create_binary_sensor(
                coordinator,
                command_type=self.ENGINEERING_INFO_COMMAND,
                name="工程資訊 - 送風(bit 2)",
                sensor_key="air_flow_status",
                device_class=BinarySensorDeviceClass.RUNNING,
                bit_mask=4,
                translation_key="dryer_air_flow_status",
                entity_registry_enabled_default=False
            ),
            self._create_binary_sensor(
                coordinator,
                command_type=self.ENGINEERING_INFO_COMMAND,
                name="工程資訊 - 鬆柔冷卻(bit 1)",
                sensor_key="soft_cooling_status",
                device_class=BinarySensorDeviceClass.RUNNING,
                bit_mask=2,
                translation_key="dryer_soft_cooling_status",
                entity_registry_enabled_default=False
            ),
            # Remote control allowance
            self._create_binary_sensor(
                coordinator,
                command_type=self.REMOTE_CONTROL_COMMAND,
                name="遠端控制允許",
                sensor_key="remote_control_allowed",
                entity_category=EntityCategory.DIAGNOSTIC,
                translation_key="dryer_remote_control_allowed"
            )
        ]
    
