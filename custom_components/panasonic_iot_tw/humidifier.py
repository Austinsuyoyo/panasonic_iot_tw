"""Humidifier platform for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, List, Optional, Callable

from homeassistant.components.humidifier import (
    HumidifierEntity,
    HumidifierEntityFeature,
    HumidifierDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import PanasonicEntity, PlatformSetupHelper
from .base import value_processors
from .const import DEHUMIDIFIER_AVAILABLE_HUMIDITY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Panasonic humidifier entities."""
    await PlatformSetupHelper.setup_platform(
        hass, config_entry, async_add_entities,
        "get_humidifier_entities", "humidifier"
    )

class PanasonicHumidifier(PanasonicEntity, HumidifierEntity):
    """Unified configurable humidifier for all types."""
    
    def __init__(
        self,
        coordinator,
        device_key: str,
        device_data: Dict[str, Any],
        name: str,
        humidifier_key: str,
        power_command: str,
        mode_command: Optional[str] = None,
        target_humidity_command: Optional[str] = None,
        current_humidity_command: Optional[str] = None,
        device_class: HumidifierDeviceClass = HumidifierDeviceClass.DEHUMIDIFIER,
        supported_features: Optional[HumidifierEntityFeature] = None,
        min_humidity: int = 30,
        max_humidity: int = 70,
        available_modes: Optional[Dict[int, str]] = None,
        humidity_mapping: Optional[Dict[int, int]] = None,
        humidity_processor: Optional[Callable[[Any], int]] = None,
        humidity_command_processor: Optional[Callable[[int], int]] = None,
        mode_processor: Optional[Callable[[Any], str]] = None,
        power_processor: Optional[Callable[[Any], bool]] = None,
        icon: Optional[str] = None,
        translation_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize the configurable humidifier entity.
        
        Args:
            coordinator: Data update coordinator
            device_key: Index of device in coordinator data
            device_data: Device information dictionary
            name: Display name for humidifier
            humidifier_key: Unique key for humidifier
            power_command: Command type for power control
            mode_command: Command type for mode control
            target_humidity_command: Command type for target humidity
            current_humidity_command: Command type for current humidity
            device_class: Humidifier device class
            supported_features: Supported humidifier features
            min_humidity: Minimum humidity
            max_humidity: Maximum humidity
            available_modes: Available operation modes mapping
            humidity_mapping: Humidity value mapping
            humidity_processor: Function to process humidity values
            humidity_command_processor: Function to process humidity commands
            mode_processor: Function to process mode values
            power_processor: Function to process power values
            icon: Icon for humidifier entity
            translation_key: Translation key for entity name
            **kwargs: Additional attributes to set on entity
        """
        # Call parent with common initialization
        super().__init__(
            coordinator, device_key, device_data,
            humidifier_key, name, translation_key, icon, **kwargs
        )
        
        # Command mappings
        self._power_command = power_command
        self._mode_command = mode_command
        self._target_humidity_command = target_humidity_command
        self._current_humidity_command = current_humidity_command
        
        # Processors
        self._humidity_processor = humidity_processor or value_processors.safe_int
        self._humidity_command_processor = humidity_command_processor or self._find_closest_humidity
        self._mode_processor = mode_processor or (lambda x: self._available_modes.get(int(x)))
        self._power_processor = power_processor or value_processors.safe_bool
        
        # Mode and humidity mappings
        self._available_modes = available_modes or {
            0: "auto",
            1: "continuous",
            2: "clothes_drying",
            3: "purify",
        }
        self._humidity_mapping = humidity_mapping or DEHUMIDIFIER_AVAILABLE_HUMIDITY
        
        # Create reverse mapping for O(1) lookup
        self._reverse_modes = self._create_reverse_mapping(self._available_modes)
        
        # Humidifier attributes
        self._attr_device_class = device_class
        self._attr_supported_features = supported_features or HumidifierEntityFeature.MODES
        
        # Humidity settings
        self._attr_min_humidity = min_humidity
        self._attr_max_humidity = max_humidity
        self._attr_available_modes = list(self._available_modes.values())
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available_with_command(self._power_command)
    
    @property
    def is_on(self) -> Optional[bool]:
        """Return true if the humidifier is on."""
        raw_value = self._get_raw_value(self._power_command)
        return self._get_processed_value(raw_value, self._power_processor)
    
    @property
    def mode(self) -> Optional[str]:
        """Return the current mode."""
        if not self._mode_command or not self._available_modes:
            return None
        return self._get_mapped_value(self._mode_command, self._available_modes)
    
    @property
    def target_humidity(self) -> Optional[int]:
        """Return the target humidity."""
        if not self._target_humidity_command:
            return None
            
        humidity = self._get_status(self._target_humidity_command)
        if humidity is not None:
            try:
                if self._humidity_mapping:
                    # Convert from device humidity index to percentage
                    humidity_index = int(humidity)
                    return self._humidity_mapping.get(humidity_index, 50)
                else:
                    return self._humidity_processor(humidity)
            except (ValueError, TypeError):
                return None
        return None
    
    @property
    def current_humidity(self) -> Optional[int]:
        """Return the current humidity."""
        return self._get_conditional_processed_value(
            self._current_humidity_command,
            self._humidity_processor
        )
    
    async def async_turn_on(self, **kwargs) -> None:
        """Turn the humidifier on."""
        await self._send_command(self._power_command, 1)
    
    async def async_turn_off(self, **kwargs) -> None:
        """Turn the humidifier off."""
        await self._send_command(self._power_command, 0)
    
    async def async_set_humidity(self, humidity: int) -> None:
        """Set the target humidity."""
        if not self._target_humidity_command:
            return
            
        try:
            device_value = self._humidity_command_processor(humidity)
            await self._send_command(self._target_humidity_command, device_value)
        except (ValueError, TypeError) as e:
            _LOGGER.error(
                "Invalid humidity %s for %s (entity_id: %s): %s", humidity, self._attr_name, self._attr_unique_id, e
            )
    
    async def async_set_mode(self, mode: str) -> None:
        """Set the mode of the humidifier."""
        if not self._mode_command or not self._reverse_modes:
            return
        await self._set_mapped_command(self._mode_command, mode, self._reverse_modes)
    
    def _find_closest_humidity(self, humidity: int) -> int:
        """Find the closest available humidity setting."""
        if not self._humidity_mapping:
            return humidity
        
        # Use min() with key function for O(n) efficiency
        return min(
            self._humidity_mapping.items(),
            key=lambda item: abs(item[1] - humidity)
        )[0]

