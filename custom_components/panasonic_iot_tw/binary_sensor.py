"""Binary sensor platform for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, Optional, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
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
    """Set up Panasonic binary_sensor entities."""
    await PlatformSetupHelper.setup_platform(
        hass, config_entry, async_add_entities,
        "get_binary_sensor_entities", "binary_sensor"
    )

class PanasonicBinarySensor(PanasonicEntity, BinarySensorEntity):
    """Unified configurable binary sensor for all types."""

    def __init__(
        self,
        coordinator,
        device_key: str,
        device_data: Dict[str, Any],
        command_type: str,
        name: str,
        sensor_key: str,
        device_class: Optional[BinarySensorDeviceClass] = None,
        icon: Optional[str] = None,
        value_processor: Optional[Callable[[Any], bool]] = None,
        data_source: str = "status",
        bit_mask: Optional[int] = None,
        translation_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize the configurable binary sensor.

        Args:
            coordinator: Data update coordinator
            device_key: Index of device in coordinator data
            device_data: Device information dictionary
            command_type: Command type for status lookup
            name: Display name for sensor (fallback when translation not available)
            sensor_key: Unique key for sensor
            device_class: Home Assistant device class
            icon: Icon for sensor
            value_processor: Function to process raw value
            data_source: Data source ("status" or direct key)
            bit_mask: Bit mask for bitwise operations
            translation_key: Translation key for entity name
            **kwargs: Additional attributes to set on entity
        """
        # Call parent with common initialization
        super().__init__(
            coordinator, device_key, device_data,
            sensor_key, name, translation_key, icon, **kwargs
        )

        # Binary sensor-specific attributes
        self._command_type = command_type
        self._data_source = data_source
        self._value_processor = value_processor or value_processors.safe_bool
        self._bit_mask = bit_mask

        # Set binary sensor-specific entity attributes
        self._attr_device_class = device_class

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available_with_command(self._command_type)

    def _get_raw_value(self, command_type: str) -> Any:
        """Get raw value from data source (override to support direct data source)."""
        try:
            if self._data_source == "status":
                return super()._get_raw_value(command_type)
            else:
                # Direct data source (live data)
                return self._current_device.get(self._data_source)
        except (KeyError, TypeError):
            return None

    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the binary sensor is on."""
        raw_value = self._get_raw_value(self._command_type)
        
        if self._bit_mask is not None:
            # Bitwise operation
            def bit_processor(value):
                return bool(int(value) & self._bit_mask)
            return self._get_processed_value(raw_value, bit_processor)
        else:
            # Use value processor
            return self._get_processed_value(raw_value, self._value_processor)

