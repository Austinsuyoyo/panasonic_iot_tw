"""Number platform for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, Optional, Callable

from homeassistant.components.number import NumberEntity
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
    """Set up Panasonic number entities."""
    await PlatformSetupHelper.setup_platform(
        hass, config_entry, async_add_entities,
        "get_number_entities", "number"
    )

class PanasonicNumber(PanasonicEntity, NumberEntity):
    """Unified configurable number for all types."""
    
    def __init__(
        self,
        coordinator,
        device_key: str,
        device_data: Dict[str, Any],
        command_type: str,
        name: str,
        number_key: str,
        min_value: float,
        max_value: float,
        step: float = 1.0,
        unit: Optional[str] = None,
        icon: Optional[str] = None,
        value_processor: Optional[Callable[[Any], float]] = None,
        command_processor: Optional[Callable[[float], int]] = None,
        readonly: bool = False,
        translation_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize the configurable number entity.
        
        Args:
            coordinator: Data update coordinator
            device_key: Index of device in coordinator data
            device_data: Device information dictionary
            command_type: Command type for status lookup
            name: Display name for number (fallback when translation not available)
            number_key: Unique key for number
            min_value: Minimum value
            max_value: Maximum value
            step: Step value
            unit: Unit of measurement
            icon: Icon for number
            value_processor: Function to process raw value for display
            command_processor: Function to process command values
            readonly: Whether the number is read-only
            translation_key: Translation key for entity name
            **kwargs: Additional attributes to set on entity
        """
        super().__init__(
            coordinator, device_key, device_data,
            number_key, name, translation_key, icon,
            native_min_value=min_value,
            native_max_value=max_value,
            native_step=step,
            native_unit_of_measurement=unit,
            **kwargs
        )

        self._command_type = command_type
        self._readonly = readonly
        self._value_processor = value_processor or value_processors.safe_float
        self._command_processor = command_processor or value_processors.process_integer_command

    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available_with_command(self._command_type)
    
    @property
    def native_value(self) -> Optional[float]:
        """Return the current value."""
        raw_value = self._get_status(self._command_type)
        return self._get_processed_value(raw_value, self._value_processor)
    
    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        if self._check_readonly("change value"):
            return

        try:
            command_value = self._command_processor(value)
            await self._send_command(self._command_type, command_value)
        except (ValueError, TypeError) as e:
            _LOGGER.error(
                "Invalid value %s for %s (entity_id: %s): %s", value, self._attr_name, self._attr_unique_id, e
            )

