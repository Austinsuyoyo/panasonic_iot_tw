"""Smart switch device logic for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, List, Optional

from ..base import BaseDevice

_LOGGER = logging.getLogger(__name__)


class SmartSwitchDevice(BaseDevice):
    """Smart switch device logic."""
    
    # Command mappings
    POWER_COMMAND = "0x70"
    
    def __init__(self, coordinator, device_key: str, device_data: Dict[str, Any]):
        """Initialize smart switch device."""
        super().__init__(coordinator, device_key, device_data)
    
    @property
    def is_on(self) -> bool:
        """Return if switch is on."""
        return self.get_boolean_status(self.POWER_COMMAND)
    
    
    def get_switch_entities(self, coordinator) -> List:
        """Return switch entities for smart switch."""
        return [
            # Main power switch
            self._create_switch(
                coordinator,
                command_type=self.POWER_COMMAND,
                name="智慧開關",
                switch_key="power",
                translation_key="smart_switch_power"
            )
        ]