"""Refrigerator device logic for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature, UnitOfEnergy

from ..base import BaseDevice, value_processors
from ..const import (
    SPECIAL_SENSOR_SUPPORTED_DEVICES,
    DEVICE_TYPE_REFRIGERATOR
)

_LOGGER = logging.getLogger(__name__)


class RefrigeratorDevice(BaseDevice):
    """Refrigerator device logic."""
    
    # Command mappings according to user specification
    FREEZER_TEMP_SETTING_COMMAND = "0x00"           # Freezer temperature setting (Low/Medium/High) Select
    REFRIGERATOR_TEMP_SETTING_COMMAND = "0x01"      # Refrigerator temperature setting (Low/Medium/High) Select  
    FREEZER_TEMP_DISPLAY_COMMAND = "0x03"           # Freezer temperature display (-40~40°C) Sensor
    REFRIGERATOR_TEMP_DISPLAY_COMMAND = "0x05"      # Refrigerator temperature display (-39~40°C) Sensor
    ECO_STATUS_COMMAND = "0x0C"                     # ECO mode status (Normal/Operating) BinarySensor
    DEFROSTING_STATUS_COMMAND = "0x50"              # Defrosting status (Normal/Defrosting) BinarySensor
    STOP_ICE_MAKING_COMMAND = "0x52"                # Stop ice making (Stop/Start) Switch
    QUICK_ICE_MAKING_COMMAND = "0x53"               # Quick ice making (Stop/Start) Switch
    FRESH_FREEZING_COMMAND = "0x56"                 # Fresh freezing mode (Normal/Cooling/Quick Cool/Quick Freeze) Sensor
    PARTIAL_FREEZING_TEMP_SETTING_COMMAND = "0x57"  # Partial freezing temperature setting (Low/Medium/High) Select
    PARTIAL_FREEZING_TEMP_DISPLAY_COMMAND = "0x58"  # Partial freezing temperature display (-39~40°C) Sensor
    WINTER_MODE_COMMAND = "0x5A"                    # Winter mode (Not activated/Operating/Available) Sensor
    SHOPPING_MODE_COMMAND = "0x5B"                  # Shopping mode (Not activated/Operating/Available) Sensor
    VACATION_MODE_COMMAND = "0x5C"                  # Vacation mode (Not activated/Operating/Available) Sensor
    NANOE_STATUS_COMMAND = "0x61"                   # nanoe status (Normal/Operating) BinarySensor
    
    @property
    def freezer_temperature(self) -> Optional[float]:
        """Return freezer temperature in Celsius."""
        temp = self.get_temperature_status(self.FREEZER_TEMP_DISPLAY_COMMAND)
        if isinstance(temp, (int, float)):
            return float(temp)
        return None
    
    @property
    def refrigerator_temperature(self) -> Optional[float]:
        """Return refrigerator temperature in Celsius."""
        temp = self.get_temperature_status(self.REFRIGERATOR_TEMP_DISPLAY_COMMAND)
        if isinstance(temp, (int, float)):
            return float(temp)
        return None
    
    @property
    def is_eco_enabled(self) -> bool:
        """Return if ECO mode is enabled."""
        return self.get_boolean_status(self.ECO_STATUS_COMMAND)
    
    @property
    def is_defrosting(self) -> bool:
        """Return if defrosting is active."""
        return self.get_boolean_status(self.DEFROSTING_STATUS_COMMAND)
    
    @property
    def is_nanoe_enabled(self) -> bool:
        """Return if nanoe is enabled."""
        return self.get_boolean_status(self.NANOE_STATUS_COMMAND)
    
    def get_sensor_entities(self, coordinator) -> List:
        """Return sensor entities for refrigerator."""
        sensors = [
            # Temperature display sensors
            self._create_sensor(
                coordinator,
                command_type=self.FREEZER_TEMP_DISPLAY_COMMAND,
                name="Freezer Temperature",
                sensor_key="freezer_temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                unit=UnitOfTemperature.CELSIUS,
                icon="mdi:thermometer",
                value_processor=value_processors.process_signed_temperature,
                translation_key="refrigerator_freezer_temperature"
            ),
            self._create_sensor(
                coordinator,
                command_type=self.REFRIGERATOR_TEMP_DISPLAY_COMMAND,
                name="Refrigerator Temperature",
                sensor_key="refrigerator_temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                unit=UnitOfTemperature.CELSIUS,
                icon="mdi:thermometer",
                value_processor=value_processors.process_signed_temperature,
                translation_key="refrigerator_refrigerator_temperature"
            ),
            self._create_sensor(
                coordinator,
                command_type=self.PARTIAL_FREEZING_TEMP_DISPLAY_COMMAND,
                name="Partial Freezing Temperature",
                sensor_key="partial_freezing_temperature",
                device_class=SensorDeviceClass.TEMPERATURE,
                state_class=SensorStateClass.MEASUREMENT,
                unit=UnitOfTemperature.CELSIUS,
                icon="mdi:thermometer",
                value_processor=value_processors.process_signed_temperature,
                translation_key="refrigerator_partial_freezing_temperature"
            )
        ]
        
        # Mode status sensors (read-only)
        sensors.extend([
            self._create_sensor(
                coordinator,
                command_type=self.FRESH_FREEZING_COMMAND,
                name="Fresh Freezing Mode",
                sensor_key="fresh_freezing_mode",
                icon="mdi:snowflake-variant",
                translation_key="refrigerator_fresh_freezing_mode"
            ),
            self._create_sensor(
                coordinator,
                command_type=self.WINTER_MODE_COMMAND,
                name="Winter Mode",
                sensor_key="winter_mode",
                icon="mdi:weather-snowy",
                translation_key="refrigerator_winter_mode"
            ),
            self._create_sensor(
                coordinator,
                command_type=self.SHOPPING_MODE_COMMAND,
                name="Shopping Mode",
                sensor_key="shopping_mode",
                icon="mdi:shopping",
                translation_key="refrigerator_shopping_mode"
            ),
            self._create_sensor(
                coordinator,
                command_type=self.VACATION_MODE_COMMAND,
                name="Vacation Mode",
                sensor_key="vacation_mode",
                icon="mdi:airplane",
                translation_key="refrigerator_vacation_mode"
            )
        ])
        
        # Add special sensors if device supports them and data is available
        special_sensors = self._create_special_sensors(coordinator)
        sensors.extend(special_sensors)
        
        return sensors
    
    def get_binary_sensor_entities(self, coordinator) -> List:
        """Return binary sensor entities for refrigerator."""
        return [
            # ECO status (Normal/Operating)
            self._create_binary_sensor(
                coordinator,
                command_type=self.ECO_STATUS_COMMAND,
                name="ECO Mode",
                sensor_key="eco_status",
                device_class=BinarySensorDeviceClass.RUNNING,
                icon="mdi:leaf",
                value_processor=value_processors.safe_bool,
                translation_key="refrigerator_eco_mode"
            ),
            # Defrosting status (Normal/Defrosting)
            self._create_binary_sensor(
                coordinator,
                command_type=self.DEFROSTING_STATUS_COMMAND,
                name="Defrosting Status",
                sensor_key="defrosting_status",
                device_class=BinarySensorDeviceClass.RUNNING,
                icon="mdi:car-defrost-rear",
                value_processor=value_processors.safe_bool,
                translation_key="refrigerator_defrosting_status"
            ),
            # nanoe status (Normal/Operating)
            self._create_binary_sensor(
                coordinator,
                command_type=self.NANOE_STATUS_COMMAND,
                name="nanoe Status",
                sensor_key="nanoe_status",
                device_class=BinarySensorDeviceClass.RUNNING,
                icon="mdi:air-filter",
                value_processor=value_processors.safe_bool,
                translation_key="refrigerator_nanoe_status"
            )
        ]
    
    def get_switch_entities(self, coordinator) -> List:
        """Return switch entities for refrigerator."""
        return [
            # Ice making controls (Stop/Start)
            self._create_switch(
                coordinator,
                command_type=self.STOP_ICE_MAKING_COMMAND,
                name="Stop Ice Making",
                switch_key="stop_ice_making",
                icon="mdi:snowflake-off",
                translation_key="refrigerator_stop_ice_making"
            ),
            self._create_switch(
                coordinator,
                command_type=self.QUICK_ICE_MAKING_COMMAND,
                name="Quick Ice Making", 
                switch_key="quick_ice_making",
                icon="mdi:snowflake",
                translation_key="refrigerator_quick_ice_making"
            )
        ]
    
    def get_select_entities(self, coordinator) -> List:
        """Return select entities for refrigerator."""
        from ..const import REFRIGERATOR_TEMPERATURE_SETTINGS
        
        return [
            # Temperature setting selects (Low/Medium/High)
            self._create_select(
                coordinator,
                command_type=self.FREEZER_TEMP_SETTING_COMMAND,
                name="Freezer Temperature Setting",
                select_key="freezer_temp_setting",
                options_dict=REFRIGERATOR_TEMPERATURE_SETTINGS,
                icon="mdi:snowflake",
                translation_key="refrigerator_freezer_temperature_setting"
            ),
            self._create_select(
                coordinator,
                command_type=self.REFRIGERATOR_TEMP_SETTING_COMMAND,
                name="Refrigerator Temperature Setting",
                select_key="refrigerator_temp_setting",
                options_dict=REFRIGERATOR_TEMPERATURE_SETTINGS,
                icon="mdi:fridge",
                translation_key="refrigerator_refrigerator_temperature_setting"
            ),
            self._create_select(
                coordinator,
                command_type=self.PARTIAL_FREEZING_TEMP_SETTING_COMMAND,
                name="Partial Freezing Temperature Setting",
                select_key="partial_freezing_temp_setting",
                options_dict=REFRIGERATOR_TEMPERATURE_SETTINGS,
                icon="mdi:food-steak",
                translation_key="refrigerator_partial_freezing_temperature_setting"
            )
        ]
    
    def _create_special_sensors(self, coordinator) -> List:
        """
        Create special sensors (energy, CO2, door) if supported and data is available.
        
        Args:
            coordinator: Data update coordinator
            
        Returns:
            List of special sensor entities
        """
        from homeassistant.const import UnitOfMass
        
        special_sensors = []
        
        # Check if this device type supports special sensors
        if DEVICE_TYPE_REFRIGERATOR not in SPECIAL_SENSOR_SUPPORTED_DEVICES:
            _LOGGER.debug("Device type %s does not support special sensors", DEVICE_TYPE_REFRIGERATOR)
            return special_sensors
        
        # Get device GWID for data lookup
        device_gwid = self.device_data.get("gwid")
        if not device_gwid:
            _LOGGER.warning("No GWID found for refrigerator device, cannot create special sensors")
            return special_sensors
        
        # Access SmartApp through coordinator to check for available data
        try:
            smart_app = coordinator.smart_app if hasattr(coordinator, 'smart_app') else None
            if not smart_app:
                _LOGGER.debug("SmartApp not accessible, skipping special sensor creation")
                return special_sensors
            
            # Create special sensors - they will show unavailable until data is fetched
            _LOGGER.info("Creating special sensors for device %s", device_gwid)
            
            # Energy consumption sensor
            special_sensors.append(self._create_sensor(
                coordinator,
                command_type="special_energy",
                name="能耗資料",
                sensor_key="energy_consumption",
                device_class=SensorDeviceClass.ENERGY,
                state_class=SensorStateClass.TOTAL_INCREASING,
                unit=UnitOfEnergy.KILO_WATT_HOUR,
                icon="mdi:lightning-bolt",
                data_source="energy",
                translation_key="refrigerator_energy_consumption"
            ))
            
            # CO2 footprint sensor
            special_sensors.append(self._create_sensor(
                coordinator,
                command_type="special_co2",
                name="碳足跡",
                sensor_key="co2_footprint",
                device_class=SensorDeviceClass.WEIGHT,
                state_class=SensorStateClass.TOTAL_INCREASING,
                unit=UnitOfMass.KILOGRAMS,
                icon="mdi:leaf",
                data_source="co2",
                translation_key="refrigerator_co2_footprint"
            ))
            
            # Door open count sensor
            special_sensors.append(self._create_sensor(
                coordinator,
                command_type="special_door",
                name="開門次數",
                sensor_key="door_open_count",
                state_class=SensorStateClass.TOTAL_INCREASING,
                icon="mdi:door-open",
                data_source="door",
                translation_key="refrigerator_door_open_count"
            ))
            
            if special_sensors:
                _LOGGER.info("Created %s special sensors for refrigerator %s", len(special_sensors), device_gwid)
            else:
                _LOGGER.info("No special sensor data available for refrigerator %s", device_gwid)
                
        except Exception as e:
            _LOGGER.error("Error creating special sensors for refrigerator: %s", e)
        
        return special_sensors
    
    
