"""Purifier device logic for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, List, Optional

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

from ..base import BaseDevice, value_processors

_LOGGER = logging.getLogger(__name__)


class PurifierDevice(BaseDevice):
    """Air purifier device logic."""
    
    # Command mappings
    POWER_COMMAND = "0x00"
    FAN_LEVEL_COMMAND = "0x01"
    NANOEX_COMMAND = "0x07"
    PM25_COMMAND = "0x50"
    
    def __init__(self, coordinator, device_key: str, device_data: Dict[str, Any]):
        """Initialize purifier device."""
        super().__init__(coordinator, device_key, device_data)
    
    @property
    def is_on(self) -> bool:
        """Return if purifier is powered on."""
        return self.get_boolean_status(self.POWER_COMMAND)

    @property
    def fan_level(self) -> Optional[int]:
        """Return current fan level."""
        return self.get_int_status(self.FAN_LEVEL_COMMAND)

    @property
    def is_nanoex_enabled(self) -> bool:
        """Return if nanoeX is enabled."""
        return self.get_boolean_status(self.NANOEX_COMMAND)

    @property
    def pm25_level(self) -> Optional[int]:
        """Return PM2.5 level in μg/m³."""
        return self.get_int_status(self.PM25_COMMAND)
    
    
    def get_sensor_entities(self, coordinator) -> List:
        """Return sensor entities for purifier."""
        return [
            # PM2.5
            self._create_sensor(
                coordinator,
                command_type=self.PM25_COMMAND,
                name="PM2.5",
                sensor_key="pm25",
                device_class=SensorDeviceClass.PM25,
                state_class=SensorStateClass.MEASUREMENT,
                unit="μg/m³",
                value_processor=value_processors.safe_int,
                translation_key="purifier_pm25"
            )
        ]
    
    def get_switch_entities(self, coordinator) -> List:
        """Return switch entities for purifier."""
        return [
            # nanoeX switch
            self._create_switch(
                coordinator,
                command_type=self.NANOEX_COMMAND,
                name="nanoeX",
                switch_key="nanoex",
                translation_key="purifier_nanoex"
            )
        ]