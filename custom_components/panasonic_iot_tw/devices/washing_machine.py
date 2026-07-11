"""Washing machine device logic for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTime

from ..base import BaseDevice, value_processors
from ..const import (
    WASHING_MACHINE_AVAILABLE_STATUS,
    WASHING_MACHINE_AVAILABLE_CYCLES
)

_LOGGER = logging.getLogger(__name__)


class WashingMachineDevice(BaseDevice):
    """Washing machine device logic."""

    # Command mappings according to user specification
    WASHING_REMAINING_TIME_COMMAND = "0x13"     # Washing remaining time (Min=0 Max=599 minutes) Sensor
    SCHEDULE_REMAINING_TIME_COMMAND = "0x15"    # Schedule remaining time (Min=0 Max=24 hours) Sensor
    ENGINEERING_INFO_COMMAND = "0x34"          # Engineering info (bitwise) 4x BinarySensor
    OPERATION_STATUS_COMMAND = "0x50"          # Operation status Sensor
    CYCLE_MESSAGE_COMMAND = "0x55"             # Cycle message Sensor
    REMOTE_CONTROL_COMMAND = "0x74"            # Remote control allowed BinarySensor

    @property
    def washing_remaining_time(self) -> Optional[int]:
        """Return washing remaining time in minutes."""
        return self.get_int_status(self.WASHING_REMAINING_TIME_COMMAND)

    @property
    def schedule_remaining_time(self) -> Optional[int]:
        """Return schedule remaining time in hours."""
        return self.get_int_status(self.SCHEDULE_REMAINING_TIME_COMMAND)

    @property
    def operation_status(self) -> Optional[int]:
        """Return current operation status."""
        return self.get_int_status(self.OPERATION_STATUS_COMMAND)

    @property
    def cycle_message(self) -> Optional[int]:
        """Return current cycle message."""
        return self.get_int_status(self.CYCLE_MESSAGE_COMMAND)

    @property
    def is_remote_control_allowed(self) -> bool:
        """Return if remote control is allowed."""
        return self.get_boolean_status(self.REMOTE_CONTROL_COMMAND)
    
    def get_sensor_entities(self, coordinator) -> List:
        """Return sensor entities for washing machine."""
        return [
            # Time sensors with formatting
            self._create_sensor(
                coordinator,
                command_type=self.WASHING_REMAINING_TIME_COMMAND,
                name="洗衣殘時間",
                sensor_key="washing_remaining_time",
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                unit=UnitOfTime.MINUTES,
                value_processor=value_processors.safe_int,
                extra_state_processor=value_processors.create_time_formatter("minutes"),
                translation_key="washing_machine_washing_remaining_time"
            ),
            self._create_sensor(
                coordinator,
                command_type=self.SCHEDULE_REMAINING_TIME_COMMAND,
                name="預約殘時間",
                sensor_key="schedule_remaining_time",
                device_class=SensorDeviceClass.DURATION,
                state_class=SensorStateClass.MEASUREMENT,
                unit=UnitOfTime.HOURS,
                value_processor=value_processors.safe_int,
                extra_state_processor=value_processors.create_time_formatter("hours"),
                translation_key="washing_machine_schedule_remaining_time"
            ),
            # Status sensors with mapping
            self._create_sensor(
                coordinator,
                command_type=self.OPERATION_STATUS_COMMAND,
                name="運轉情報",
                sensor_key="operation_status",
                device_class=SensorDeviceClass.ENUM,
                options=list(dict.fromkeys(WASHING_MACHINE_AVAILABLE_STATUS.values())),
                value_processor=value_processors.create_status_mapping_processor(WASHING_MACHINE_AVAILABLE_STATUS),
                translation_key="washing_machine_operation_status"
            ),
            self._create_sensor(
                coordinator,
                command_type=self.CYCLE_MESSAGE_COMMAND,
                name="行程別訊息",
                sensor_key="cycle_message",
                device_class=SensorDeviceClass.ENUM,
                options=list(dict.fromkeys(WASHING_MACHINE_AVAILABLE_CYCLES.values())),
                value_processor=value_processors.create_status_mapping_processor(WASHING_MACHINE_AVAILABLE_CYCLES),
                translation_key="washing_machine_cycle_message"
            )
        ]
    
    def get_binary_sensor_entities(self, coordinator) -> List:
        """Return binary sensor entities for washing machine."""
        return [
            # Engineering info 0x34 - 4 bitwise sensors
            self._create_binary_sensor(
                coordinator,
                command_type=self.ENGINEERING_INFO_COMMAND,
                name="工程模式 - 預洗(bit 7)",
                sensor_key="prewash_status",
                device_class=BinarySensorDeviceClass.RUNNING,
                bit_mask=128,
                translation_key="washing_machine_prewash_status",
                entity_registry_enabled_default=False
            ),
            self._create_binary_sensor(
                coordinator,
                command_type=self.ENGINEERING_INFO_COMMAND,
                name="工程模式 - 洗衣(bit 6)",
                sensor_key="washing_status",
                device_class=BinarySensorDeviceClass.RUNNING,
                bit_mask=64,
                translation_key="washing_machine_washing_status",
                entity_registry_enabled_default=False
            ),
            self._create_binary_sensor(
                coordinator,
                command_type=self.ENGINEERING_INFO_COMMAND,
                name="工程模式 - 洗清(bit 5)",
                sensor_key="rinsing_status",
                device_class=BinarySensorDeviceClass.RUNNING,
                bit_mask=32,
                translation_key="washing_machine_rinsing_status",
                entity_registry_enabled_default=False
            ),
            self._create_binary_sensor(
                coordinator,
                command_type=self.ENGINEERING_INFO_COMMAND,
                name="工程模式 - 脫水(bit 4)",
                sensor_key="spinning_status",
                device_class=BinarySensorDeviceClass.RUNNING,
                bit_mask=16,
                translation_key="washing_machine_spinning_status",
                entity_registry_enabled_default=False
            ),
            # Remote control allowance
            self._create_binary_sensor(
                coordinator,
                command_type=self.REMOTE_CONTROL_COMMAND,
                name="遠端控制允許",
                sensor_key="remote_control_allowed",
                device_class=BinarySensorDeviceClass.CONNECTIVITY,
                value_processor=value_processors.process_remote_control,
                translation_key="washing_machine_remote_control_allowed"
            )
        ]
    
