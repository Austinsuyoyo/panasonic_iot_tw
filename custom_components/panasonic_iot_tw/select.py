"""Select platform for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, Optional, Callable

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import PanasonicEntity, PlatformSetupHelper

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Panasonic select entities."""
    await PlatformSetupHelper.setup_platform(
        hass, config_entry, async_add_entities,
        "get_select_entities", "select"
    )

class PanasonicSelect(PanasonicEntity, SelectEntity):
    """Unified configurable select for all types."""
    
    def __init__(
        self,
        coordinator,
        device_key: str,
        device_data: Dict[str, Any],
        command_type: str,
        name: str,
        select_key: str,
        options_dict: Dict[int, str],
        icon: Optional[str] = None,
        readonly: bool = False,
        command_processor: Optional[Callable[[str], int]] = None,
        translation_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize the configurable select entity.
        
        Args:
            coordinator: Data update coordinator
            device_key: Key of device in coordinator data (device_id)
            device_data: Device information dictionary
            command_type: Command type for status lookup
            name: Display name for select (fallback when translation not available)
            select_key: Unique key for select
            options_dict: Dictionary mapping values to option names
            icon: Icon for select
            readonly: Whether the select is read-only
            command_processor: Function to process command values
            translation_key: Translation key for entity name
            **kwargs: Additional attributes to set on entity
        """
        super().__init__(
            coordinator, device_key, device_data,
            select_key, name, translation_key, icon,
            options=list(options_dict.values()), **kwargs
        )

        self._command_type = command_type
        self._options_dict = options_dict
        self._reverse_options = {v: k for k, v in options_dict.items()}  # Reverse mapping for O(1) lookup
        self._readonly = readonly
        self._command_processor = command_processor or self._get_command_from_option

    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available_with_command(self._command_type)
    
    @property
    def current_option(self) -> Optional[str]:
        """Return the current selected option."""
        value = self._get_status(self._command_type)
        
        def option_processor(val):
            return self._options_dict.get(int(val))
        
        return self._get_processed_value(value, option_processor)
    
    async def async_select_option(self, option: str) -> None:
        """Select the option."""
        if self._check_readonly("change option"):
            return

        # O(1) lookup using reverse mapping
        option_key = self._reverse_options.get(option)

        if option_key is not None:
            await self._send_command(self._command_type, option_key)
        else:
            _LOGGER.error(
                "Unknown option %s for %s (entity_id: %s)", option, self._attr_name, self._attr_unique_id
            )
    
    def _get_command_from_option(self, option: str) -> int:
        """Get command value from option string."""
        return self._reverse_options.get(option, 0)

