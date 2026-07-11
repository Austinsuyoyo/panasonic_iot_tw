"""Switch platform for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, Optional, Callable

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import PanasonicEntity, PlatformSetupHelper
from .base import value_processors

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Panasonic switch entities."""
    await PlatformSetupHelper.setup_platform(
        hass, config_entry, async_add_entities,
        "get_switch_entities", "switch"
    )

class PanasonicSwitch(PanasonicEntity, SwitchEntity):
    """Unified configurable switch for all types."""
    
    def __init__(
        self,
        coordinator,
        device_index: int,
        device_data: Dict[str, Any],
        command_type: str,
        name: str,
        switch_key: str,
        icon: Optional[str] = None,
        value_processor: Optional[Callable[[Any], bool]] = None,
        command_processor: Optional[Callable[[bool], int]] = None,
        translation_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize the configurable switch.
        
        Args:
            coordinator: Data update coordinator
            device_index: Index of device in coordinator data
            device_data: Device information dictionary
            command_type: Command type for status lookup
            name: Display name for switch (fallback when translation not available)
            switch_key: Unique key for switch
            icon: Icon for switch
            value_processor: Function to process raw value for state
            command_processor: Function to process command values
            translation_key: Translation key for entity name
            **kwargs: Additional attributes to set on entity
        """
        super().__init__(
            coordinator, device_index, device_data,
            switch_key, name, translation_key, icon, **kwargs
        )

        self._command_type = command_type
        self._value_processor = value_processor or value_processors.safe_bool
        self._command_processor = command_processor or value_processors.process_command_boolean

    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available_with_command(self._command_type)

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if switch is on."""
        raw_value = self._get_raw_value(self._command_type)
        return self._get_processed_value(raw_value, self._value_processor)
    
    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        command_value = self._command_processor(True)
        await self._send_command(self._command_type, command_value)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        command_value = self._command_processor(False)
        await self._send_command(self._command_type, command_value)

