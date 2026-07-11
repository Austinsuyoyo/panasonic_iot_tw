"""Air conditioner device logic for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature

from ..base import BaseDevice, value_processors
from ..const import (
    CLIMATE_AVAILABLE_FAN_MODE,
    CLIMATE_AVAILABLE_SWING_MODE
)

_LOGGER = logging.getLogger(__name__)


class AirConditionerDevice(BaseDevice):
    """Air conditioner device logic."""
    
    # Command mappings
    POWER_COMMAND = "0x00"
    MODE_COMMAND = "0x01"
    FAN_COMMAND = "0x02"
    TARGET_TEMP_COMMAND = "0x03"
    CURRENT_TEMP_COMMAND = "0x04"
    SLEEP_MODE_COMMAND = "0x05"
    NANOE_COMMAND = "0x08"
    HORIZONTAL_SWING_COMMAND = "0x0F"
    VERTICAL_SWING_COMMAND = "0x11"
    ECONAVI_COMMAND = "0x1B"
    OUTDOOR_TEMP_COMMAND = "0x21"
    PM25_COMMAND = "0x37"
    
    # Mode mappings
    MODE_MAPPING = {
        0: "cool",
        1: "dry", 
        2: "fan_only",
        3: "auto",
        4: "heat",
    }
    
    def __init__(self, coordinator, device_index: int, device_data: Dict[str, Any]):
        """Initialize air conditioner device."""
        super().__init__(coordinator, device_index, device_data)
    
    @property
    def is_on(self) -> bool:
        """Return if AC is powered on."""
        return self.get_boolean_status(self.POWER_COMMAND)
    
    @property
    def current_temperature(self) -> Optional[float]:
        """Return current temperature in Celsius."""
        temp = self.get_temperature_status(self.CURRENT_TEMP_COMMAND)
        if isinstance(temp, (int, float)):
            return float(temp)
        return None
    
    @property
    def target_temperature(self) -> Optional[float]:
        """Return target temperature in Celsius."""
        temp = self.get_temperature_status(self.TARGET_TEMP_COMMAND)
        if isinstance(temp, (int, float)):
            return float(temp)
        return None
    
    @property
    def outdoor_temperature(self) -> Optional[float]:
        """Return outdoor temperature in Celsius."""
        temp = self.get_temperature_status(self.OUTDOOR_TEMP_COMMAND)
        if isinstance(temp, (int, float)):
            return float(temp)
        return None
    
    @property
    def current_mode(self) -> Optional[str]:
        """Return current operation mode."""
        mode_value = self.get_int_status(self.MODE_COMMAND)
        if isinstance(mode_value, int):
            return self.MODE_MAPPING.get(mode_value)
        return None
    
    @property
    def fan_level(self) -> Optional[int]:
        """Return current fan level (0-5)."""
        return self.get_int_status(self.FAN_COMMAND)
    
    @property
    def horizontal_swing_position(self) -> Optional[int]:
        """Return horizontal swing position."""
        return self.get_int_status(self.HORIZONTAL_SWING_COMMAND)
    
    @property
    def vertical_swing_position(self) -> Optional[int]:
        """Return vertical swing position."""
        return self.get_int_status(self.VERTICAL_SWING_COMMAND)
    
    @property
    def is_nanoe_enabled(self) -> bool:
        """Return if nanoeX is enabled."""
        return self.get_boolean_status(self.NANOE_COMMAND)
    
    @property
    def is_econavi_enabled(self) -> bool:
        """Return if ECONAVI is enabled."""
        return self.get_boolean_status(self.ECONAVI_COMMAND)
    
    @property
    def is_sleep_mode_enabled(self) -> bool:
        """Return if sleep mode is enabled."""
        return self.get_boolean_status(self.SLEEP_MODE_COMMAND)
    
    @property
    def pm25_level(self) -> Optional[int]:
        """Return PM2.5 level in μg/m³."""
        return self.get_int_status(self.PM25_COMMAND)
    
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Return a summary of device status."""
        return {
            "power": self.is_on,
            "mode": self.current_mode,
            "current_temperature": self.current_temperature,
            "target_temperature": self.target_temperature,
            "outdoor_temperature": self.outdoor_temperature,
            "fan_level": self.fan_level,
            "nanoe_enabled": self.is_nanoe_enabled,
            "econavi_enabled": self.is_econavi_enabled,
            "sleep_mode": self.is_sleep_mode_enabled,
            "pm25": self.pm25_level,
            "available": self.is_device_available(),
        }
    
    def get_sensor_entities(self, coordinator) -> List:
        """Return sensor entities for air conditioner."""
        return [
            # Current temperature
            self._create_sensor(
                coordinator,
                command_type=self.CURRENT_TEMP_COMMAND,
                name="室內溫度",
                sensor_key="current_temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                unit=UnitOfTemperature.CELSIUS,
                icon="mdi:thermometer",
                value_processor=value_processors.process_signed_temperature,
                translation_key="air_conditioner_current_temperature"
            ),
            # Outdoor temperature
            self._create_sensor(
                coordinator,
                command_type=self.OUTDOOR_TEMP_COMMAND,
                name="室外溫度",
                sensor_key="outdoor_temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                unit=UnitOfTemperature.CELSIUS,
                icon="mdi:thermometer",
                value_processor=value_processors.process_signed_temperature,
                translation_key="air_conditioner_outdoor_temperature"
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
                translation_key="air_conditioner_pm25"
            )
        ]
    
    def get_binary_sensor_entities(self, coordinator) -> List:
        """Return binary sensor entities for air conditioner."""
        # AC doesn't have binary sensors in current implementation
        return []
    
    def get_switch_entities(self, coordinator) -> List:
        """Return switch entities for air conditioner."""
        return [
            # nanoeX
            self._create_switch(
                coordinator,
                command_type="0x08",
                name="nanoeX",
                switch_key="nanoex",
                icon="mdi:atom"
            ),
            # ECONAVI
            self._create_switch(
                coordinator,
                command_type="0x1B",
                name="ECONAVI",
                switch_key="econavi",
                icon="mdi:leaf"
            ),
            # Buzzer
            self._create_switch(
                coordinator,
                command_type="0x1E",
                name="操作提示音",
                switch_key="buzzer",
                icon="mdi:volume-high"
            ),
            # Turbo mode
            self._create_switch(
                coordinator,
                command_type="0x1A",
                name="急速模式",
                switch_key="turbo",
                icon="mdi:clock-fast"
            ),
            # Self clean
            self._create_switch(
                coordinator,
                command_type="0x18",
                name="自體淨",
                switch_key="self_clean",
                icon="mdi:broom"
            ),
            # Sleep mode
            self._create_switch(
                coordinator,
                command_type=self.SLEEP_MODE_COMMAND,
                name="舒眠模式",
                switch_key="sleep",
                icon="mdi:sleep"
            ),
            # Mold prevention
            self._create_switch(
                coordinator,
                command_type="0x17",
                name="乾燥防霉",
                switch_key="mold_prevention",
                icon="mdi:weather-windy",
                translation_key="air_conditioner_mold_prevention"
            ),
            # Motion detection
            self._create_switch(
                coordinator,
                command_type="0x19",
                name="動向感應",
                switch_key="motion_detection",
                icon="mdi:motion-sensor",
                translation_key="air_conditioner_motion_detection"
            ),
            # Indicator light
            self._create_switch(
                coordinator,
                command_type="0x1F",
                name="機體燈光",
                switch_key="indicator_light",
                icon="mdi:lightbulb-on-outline",
                translation_key="air_conditioner_indicator_light"
            )
        ]
    
    def get_select_entities(self, coordinator) -> List:
        """Return select entities for air conditioner."""
        return [
            # Fan mode
            self._create_select(
                coordinator,
                command_type="0x02",
                name="風量設定",
                select_key="fan_mode",
                options_dict=CLIMATE_AVAILABLE_FAN_MODE,
                icon="mdi:fan",
                translation_key="air_conditioner_fan_mode"
            ),
            # Horizontal swing
            self._create_select(
                coordinator,
                command_type="0x0F",
                name="水平擺風",
                select_key="horizontal_swing",
                options_dict=CLIMATE_AVAILABLE_SWING_MODE,
                icon="mdi:arrow-left-right",
                translation_key="air_conditioner_horizontal_swing"
            ),
            # Vertical swing
            self._create_select(
                coordinator,
                command_type="0x11",
                name="垂直擺風",
                select_key="vertical_swing",
                options_dict=CLIMATE_AVAILABLE_SWING_MODE,
                icon="mdi:arrow-up-down",
                translation_key="air_conditioner_vertical_swing"
            )
        ]
    
    def get_number_entities(self, coordinator) -> List:
        """Return number entities for air conditioner."""
        return [
            # On timer
            self._create_number(
                coordinator,
                command_type="0x0B",
                name="定時開機",
                number_key="on_timer",
                min_value=0,
                max_value=1440,
                step=1,
                unit="分鐘",
                icon="mdi:timer",
                translation_key="air_conditioner_on_timer"
            ),
            # Off timer
            self._create_number(
                coordinator,
                command_type="0x0C",
                name="定時關機",
                number_key="off_timer",
                min_value=0,
                max_value=1440,
                step=1,
                unit="分鐘",
                icon="mdi:timer-off",
                translation_key="air_conditioner_off_timer"
            )
        ]
    
    def get_button_entities(self, coordinator) -> List:
        """Return button entities for air conditioner."""
        return [
            # Self clean button
            self._create_button(
                coordinator,
                command_type="0x18",
                name="自體淨",
                button_key="self_clean",
                icon="mdi:broom",
                translation_key="air_conditioner_self_clean_button"
            )
        ]
    
    def get_climate_entities(self, coordinator) -> List:
        """Return climate entities for air conditioner."""
        return [
            self._create_climate(
                coordinator,
                name="空調控制",
                climate_key="air_conditioner",
                power_command=self.POWER_COMMAND,
                mode_command=self.MODE_COMMAND,
                target_temp_command=self.TARGET_TEMP_COMMAND,
                current_temp_command=self.CURRENT_TEMP_COMMAND,
                fan_mode_command=self.FAN_COMMAND,
                hvac_mode_mapping=self.MODE_MAPPING,
                min_temp=16.0,
                max_temp=30.0,
                temp_step=1.0,
                translation_key="air_conditioner_climate"
            )
        ]