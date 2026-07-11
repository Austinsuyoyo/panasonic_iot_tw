"""Dehumidifier device logic for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE

from ..base import BaseDevice, value_processors
from ..const import (
    DEHUMIDIFIER_AVAILABLE_HUMIDITY
)

_LOGGER = logging.getLogger(__name__)


class DehumidifierDevice(BaseDevice):
    """Dehumidifier device logic."""
    
    # Command mappings
    POWER_COMMAND = "0x00"
    MODE_COMMAND = "0x01"
    OFF_TIMER_COMMAND = "0x02"
    TARGET_HUMIDITY_COMMAND = "0x04"
    HUMIDITY_SENSOR_COMMAND = "0x07"
    FAN_DIRECTION_COMMAND = "0x09"
    TANK_STATUS_COMMAND = "0x0A"
    NANOE_COMMAND = "0x0D"
    FAN_MODE_COMMAND = "0x0E"
    BUZZER_COMMAND = "0x18"
    PM25_COMMAND = "0x53"
    ON_TIMER_COMMAND = "0x55"
    
    # Mode mappings
    MODE_MAPPING = {
        0: "auto",
        1: "continuous",
        2: "clothes_drying",
        3: "purify",
    }
    
    # Humidity mappings
    HUMIDITY_MAPPING = {
        0: 40, 1: 45, 2: 50, 3: 55, 4: 60, 5: 65, 6: 70
    }
    
    def __init__(self, coordinator, device_key: str, device_data: Dict[str, Any]):
        """Initialize dehumidifier device."""
        super().__init__(coordinator, device_key, device_data)
    
    @property
    def is_on(self) -> bool:
        """Return if dehumidifier is powered on."""
        return self.get_boolean_status(self.POWER_COMMAND)
    
    @property
    def current_mode(self) -> Optional[str]:
        """Return current operation mode."""
        mode_value = self.get_int_status(self.MODE_COMMAND)
        if isinstance(mode_value, int):
            return self.MODE_MAPPING.get(mode_value)
        return None
    
    @property
    def target_humidity(self) -> Optional[int]:
        """Return target humidity percentage."""
        humidity_index = self.get_int_status(self.TARGET_HUMIDITY_COMMAND)
        if isinstance(humidity_index, int):
            return self.HUMIDITY_MAPPING.get(humidity_index)
        return None
    
    @property
    def current_humidity(self) -> Optional[int]:
        """Return current humidity percentage."""
        return self.get_int_status(self.HUMIDITY_SENSOR_COMMAND)
    
    @property
    def is_tank_full(self) -> bool:
        """Return if water tank is full."""
        return self.get_boolean_status(self.TANK_STATUS_COMMAND)
    
    @property
    def is_nanoe_enabled(self) -> bool:
        """Return if nanoe is enabled."""
        return self.get_boolean_status(self.NANOE_COMMAND)
    
    @property
    def is_buzzer_enabled(self) -> bool:
        """Return if buzzer is enabled."""
        return self.get_boolean_status(self.BUZZER_COMMAND)
    
    @property
    def fan_mode(self) -> Optional[int]:
        """Return current fan mode."""
        return self.get_int_status(self.FAN_MODE_COMMAND)
    
    @property
    def fan_direction(self) -> Optional[int]:
        """Return fan direction setting."""
        return self.get_int_status(self.FAN_DIRECTION_COMMAND)
    
    @property
    def pm25_level(self) -> Optional[int]:
        """Return PM2.5 level in μg/m³."""
        return self.get_int_status(self.PM25_COMMAND)
    
    @property
    def on_timer(self) -> Optional[int]:
        """Return on timer value in hours."""
        return self.get_int_status(self.ON_TIMER_COMMAND)
    
    @property
    def off_timer(self) -> Optional[int]:
        """Return off timer value in hours."""
        return self.get_int_status(self.OFF_TIMER_COMMAND)
    
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Return a summary of device status."""
        return {
            "power": self.is_on,
            "mode": self.current_mode,
            "current_humidity": self.current_humidity,
            "target_humidity": self.target_humidity,
            "tank_full": self.is_tank_full,
            "nanoe_enabled": self.is_nanoe_enabled,
            "buzzer_enabled": self.is_buzzer_enabled,
            "fan_mode": self.fan_mode,
            "pm25": self.pm25_level,
            "available": self.is_device_available(),
        }
    
    def get_sensor_entities(self, coordinator) -> List:
        """Return sensor entities for dehumidifier."""
        return [
            # Humidity
            self._create_sensor(
                coordinator,
                command_type=self.HUMIDITY_SENSOR_COMMAND,
                name="環境濕度",
                sensor_key="humidity",
                device_class=SensorDeviceClass.HUMIDITY,
                state_class=SensorStateClass.MEASUREMENT,
                unit=PERCENTAGE,
                icon="mdi:water-percent",
                value_processor=value_processors.safe_int,
                translation_key="dehumidifier_humidity"
            ),
            # PM2.5
            self._create_sensor(
                coordinator,
                command_type=self.PM25_COMMAND,
                name="PM2.5",
                sensor_key="pm25",
                device_class=SensorDeviceClass.PM25,
                state_class=SensorStateClass.MEASUREMENT,
                unit="μg/m³",
                icon="mdi:air-filter",
                value_processor=value_processors.safe_int,
                translation_key="dehumidifier_pm25"
            )
        ]
    
    def get_binary_sensor_entities(self, coordinator) -> List:
        """Return binary sensor entities for dehumidifier."""
        return [
            # Water tank full
            self._create_binary_sensor(
                coordinator,
                command_type=self.TANK_STATUS_COMMAND,
                name="水箱滿水",
                sensor_key="tank_full",
                device_class=BinarySensorDeviceClass.PROBLEM,
                icon="mdi:cup-water",
                translation_key="dehumidifier_tank_full"
            )
        ]
    
    def get_switch_entities(self, coordinator) -> List:
        """Return switch entities for dehumidifier."""
        return [
            # nanoe
            self._create_switch(
                coordinator,
                command_type=self.NANOE_COMMAND,
                name="nanoe",
                switch_key="nanoe",
                icon="mdi:atom",
                translation_key="dehumidifier_nanoe"
            ),
            # Buzzer
            self._create_switch(
                coordinator,
                command_type=self.BUZZER_COMMAND,
                name="操作提示音",
                switch_key="buzzer",
                icon="mdi:volume-high",
                translation_key="dehumidifier_buzzer"
            )
        ]
    
    def get_select_entities(self, coordinator) -> List:
        """Return select entities for dehumidifier."""
        operation_modes = {
            0: "auto",
            1: "continuous",
            2: "clothes_drying",
            3: "purify",
        }
        fan_directions = {
            0: "stop",
            1: "swing",
            2: "horizontal",
            3: "up",
            4: "down"
        }
        
        return [
            # Operation mode
            self._create_select(
                coordinator,
                command_type=self.MODE_COMMAND,
                name="運轉模式",
                select_key="operation_mode",
                options_dict=operation_modes,
                icon="mdi:cog",
                translation_key="dehumidifier_operation_mode"
            ),
            # Fan direction
            self._create_select(
                coordinator,
                command_type=self.FAN_DIRECTION_COMMAND,
                name="風向設定",
                select_key="fan_direction",
                options_dict=fan_directions,
                icon="mdi:arrow-up-down",
                translation_key="dehumidifier_fan_direction"
            )
        ]
    
    def get_number_entities(self, coordinator) -> List:
        """Return number entities for dehumidifier."""
        from ..const import DEHUMIDIFIER_MIN_HUMD, DEHUMIDIFIER_MAX_HUMD
        
        return [
            # Target humidity
            self._create_number(
                coordinator,
                command_type=self.TARGET_HUMIDITY_COMMAND,
                name="目標濕度",
                number_key="target_humidity",
                min_value=DEHUMIDIFIER_MIN_HUMD,
                max_value=DEHUMIDIFIER_MAX_HUMD,
                step=5,
                unit="%",
                icon="mdi:water-percent",
                translation_key="dehumidifier_target_humidity"
            ),
            # On timer
            self._create_number(
                coordinator,
                command_type=self.ON_TIMER_COMMAND,
                name="定時開機",
                number_key="on_timer",
                min_value=0,
                max_value=12,
                step=1,
                unit="小時",
                icon="mdi:timer",
                translation_key="dehumidifier_on_timer"
            ),
            # Off timer
            self._create_number(
                coordinator,
                command_type=self.OFF_TIMER_COMMAND,
                name="定時關機",
                number_key="off_timer",
                min_value=0,
                max_value=12,
                step=1,
                unit="小時",
                icon="mdi:timer-off",
                translation_key="dehumidifier_off_timer"
            )
        ]
    
    def get_button_entities(self, coordinator) -> List:
        """Return button entities for dehumidifier."""
        return [
            # Reset filter button
            self._create_button(
                coordinator,
                command_type="0xFF",
                name="重置濾網",
                button_key="reset_filter",
                icon="mdi:air-filter",
                translation_key="dehumidifier_reset_filter"
            )
        ]
    
    def get_humidifier_entities(self, coordinator) -> List:
        """Return humidifier entities for dehumidifier."""
        return [
            self._create_humidifier(
                coordinator,
                name="除濕控制",
                humidifier_key="dehumidifier",
                power_command=self.POWER_COMMAND,
                mode_command=self.MODE_COMMAND,
                target_humidity_command=self.TARGET_HUMIDITY_COMMAND,
                current_humidity_command=self.HUMIDITY_SENSOR_COMMAND,
                device_class="dehumidifier",
                min_humidity=30,
                max_humidity=70,
                available_modes=self.MODE_MAPPING,
                humidity_mapping=self.HUMIDITY_MAPPING,
                translation_key="dehumidifier_control"
            )
        ]