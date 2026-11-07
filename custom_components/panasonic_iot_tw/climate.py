"""Climate platform for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, List, Optional, Callable

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import PanasonicEntity, PlatformSetupHelper
from .base import value_processors
from .const import (
    CLIMATE_AVAILABLE_MODE,
    CLIMATE_AVAILABLE_FAN_MODE,
    CLIMATE_AVAILABLE_SWING_MODE,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Panasonic climate entities."""
    await PlatformSetupHelper.setup_platform(
        hass, config_entry, async_add_entities,
        "get_climate_entities", "climate"
    )

class PanasonicClimate(PanasonicEntity, ClimateEntity):
    """Unified configurable climate for all types."""
    
    def __init__(
        self,
        coordinator,
        device_key: str,
        device_data: Dict[str, Any],
        name: str,
        climate_key: str,
        power_command: str,
        mode_command: Optional[str] = None,
        target_temp_command: Optional[str] = None,
        current_temp_command: Optional[str] = None,
        fan_mode_command: Optional[str] = None,
        swing_mode_command: Optional[str] = None,
        hvac_modes: Optional[List[HVACMode]] = None,
        fan_modes: Optional[List[str]] = None,
        swing_modes: Optional[List[str]] = None,
        supported_features: Optional[ClimateEntityFeature] = None,
        min_temp: float = 16.0,
        max_temp: float = 30.0,
        temp_step: float = 1.0,
        temp_unit: str = UnitOfTemperature.CELSIUS,
        hvac_mode_mapping: Optional[List[Dict[str, Any]]] = None,
        fan_mode_mapping: Optional[Dict] = None,
        swing_mode_mapping: Optional[Dict] = None,
        temp_processor: Optional[Callable[[Any], float]] = None,
        temp_command_processor: Optional[Callable[[float], int]] = None,
        icon: Optional[str] = None,
        translation_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize the configurable climate entity.
        
        Args:
            coordinator: Data update coordinator
            device_key: Key of device in coordinator data (device_id)
            device_data: Device information dictionary
            name: Display name for climate
            climate_key: Unique key for climate
            power_command: Command type for power control
            mode_command: Command type for HVAC mode
            target_temp_command: Command type for target temperature
            current_temp_command: Command type for current temperature
            fan_mode_command: Command type for fan mode
            swing_mode_command: Command type for swing mode
            hvac_modes: Available HVAC modes
            fan_modes: Available fan modes
            swing_modes: Available swing modes
            supported_features: Supported climate features
            min_temp: Minimum temperature
            max_temp: Maximum temperature
            temp_step: Temperature step
            temp_unit: Temperature unit
            hvac_mode_mapping: Mapping for HVAC modes
            fan_mode_mapping: Mapping for fan modes
            swing_mode_mapping: Mapping for swing modes
            temp_processor: Function to process temperature values
            temp_command_processor: Function to process temperature commands
            icon: Icon for climate entity
            translation_key: Translation key for entity name
            **kwargs: Additional attributes to set on entity
        """
        # Call parent with common initialization
        super().__init__(
            coordinator, device_key, device_data,
            climate_key, name, translation_key, icon, **kwargs
        )
        
        # Command mappings
        self._power_command = power_command
        self._mode_command = mode_command
        self._target_temp_command = target_temp_command
        self._current_temp_command = current_temp_command
        self._fan_mode_command = fan_mode_command
        self._swing_mode_command = swing_mode_command
        
        # Processors
        # Whole degrees: the official CommandList gives the AC's 0x03 as a
        # 16-30 range in degrees, and its 0x04 sensor reads the same way
        self._temp_processor = temp_processor or value_processors.process_signed_temperature
        self._temp_command_processor = temp_command_processor or value_processors.process_temperature_command
        
        # Mode mappings
        self._hvac_mode_mapping = hvac_mode_mapping or CLIMATE_AVAILABLE_MODE
        self._fan_mode_mapping = fan_mode_mapping or CLIMATE_AVAILABLE_FAN_MODE
        self._swing_mode_mapping = swing_mode_mapping or CLIMATE_AVAILABLE_SWING_MODE
        
        # Create reverse mappings for O(1) lookup
        self._reverse_fan_mode_mapping = self._create_reverse_mapping(self._fan_mode_mapping)
        self._reverse_swing_mode_mapping = self._create_reverse_mapping(self._swing_mode_mapping)
        
        # Create HVAC mode mappings from a list of {"key", "mappingCode"} dicts;
        # a non-dict entry raises here, an entry missing either key is ignored
        self._hvac_code_to_mode: Dict[int, HVACMode] = {}
        self._hvac_mode_to_code: Dict[HVACMode, int] = {}
        for mode_info in self._hvac_mode_mapping:
            code = mode_info.get("mappingCode")
            mode = mode_info.get("key")
            if code is not None and mode is not None:
                self._hvac_code_to_mode[code] = mode
                self._hvac_mode_to_code[mode] = code
        
        # Climate features: only advertise controls backed by a command, or HA
        # shows controls that silently do nothing
        if supported_features is None:
            supported_features = ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
            if target_temp_command:
                supported_features |= ClimateEntityFeature.TARGET_TEMPERATURE
            if fan_mode_command:
                supported_features |= ClimateEntityFeature.FAN_MODE
            if swing_mode_command:
                supported_features |= ClimateEntityFeature.SWING_MODE
        self._attr_supported_features = supported_features
        
        # Temperature settings
        self._attr_native_temperature_unit = temp_unit
        self._attr_min_temp = min_temp
        self._attr_max_temp = max_temp
        self._attr_target_temperature_step = temp_step
        
        # Available modes
        if hvac_modes:
            self._attr_hvac_modes = hvac_modes
        elif self._hvac_mode_to_code:
            self._attr_hvac_modes = list(self._hvac_mode_to_code)
        else:
            self._attr_hvac_modes = [HVACMode.OFF, HVACMode.AUTO]
            
        if fan_modes:
            self._attr_fan_modes = fan_modes
        elif self._fan_mode_mapping:
            self._attr_fan_modes = list(self._fan_mode_mapping.values())
        else:
            self._attr_fan_modes = ["Auto"]
            
        if swing_modes:
            self._attr_swing_modes = swing_modes
        elif self._swing_mode_mapping:
            self._attr_swing_modes = list(self._swing_mode_mapping.values())
        else:
            self._attr_swing_modes = ["Auto"]
    
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._available_with_command(self._power_command)
    
    @property
    def native_current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self._get_conditional_processed_value(
            self._current_temp_command,
            self._temp_processor
        )
    
    @property
    def native_target_temperature(self) -> Optional[float]:
        """Return the target temperature."""
        return self._get_conditional_processed_value(
            self._target_temp_command,
            self._temp_processor
        )
    
    def _power(self) -> Optional[int]:
        """Power register as an int; DeviceGetInfo reports every status as a string."""
        return self._get_conditional_processed_value(self._power_command, value_processors.safe_int)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        power = self._power()
        
        if power == 0:
            return HVACMode.OFF
        
        if self._mode_command and self._hvac_code_to_mode:
            mode_code = self._get_status(self._mode_command)
            if mode_code is not None:
                try:
                    mode_code_int = int(mode_code)
                    return self._hvac_code_to_mode.get(mode_code_int, HVACMode.AUTO)
                except (ValueError, TypeError):
                    pass
        
        return HVACMode.AUTO if power == 1 else HVACMode.OFF
    
    @property
    def fan_mode(self) -> Optional[str]:
        """Return current fan mode."""
        if not self._fan_mode_command or not self._fan_mode_mapping:
            return None
        return self._get_mapped_value(self._fan_mode_command, self._fan_mode_mapping)
    
    @property
    def swing_mode(self) -> Optional[str]:
        """Return current swing mode."""
        if not self._swing_mode_command or not self._swing_mode_mapping:
            return None
        return self._get_mapped_value(self._swing_mode_command, self._swing_mode_mapping)
    
    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature, switching mode first when the call names one."""
        if (hvac_mode := kwargs.get(ATTR_HVAC_MODE)) is not None:
            await self.async_set_hvac_mode(hvac_mode)
        if not self._target_temp_command:
            return
            
        if ATTR_TEMPERATURE in kwargs:
            temp = kwargs[ATTR_TEMPERATURE]
            try:
                device_temp = self._temp_command_processor(temp)
                await self._send_command(self._target_temp_command, device_temp)
            except (ValueError, TypeError) as e:
                _LOGGER.error(
                    "Invalid temperature %s for %s (entity_id: %s): %s", temp, self._attr_name, self._attr_unique_id, e
                )
    
    async def async_turn_on(self) -> None:
        """Send only the power command; HA's default would also switch the mode to heat."""
        await self._send_command(self._power_command, 1)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            # Turn off the device
            await self._send_command(self._power_command, 0)
        else:
            # Power on unless the unit is known to be on
            if self._power() != 1:
                await self._send_command(self._power_command, 1)
            
            # Set the mode if mode command is available
            if self._mode_command and hvac_mode in self._hvac_mode_to_code:
                mode_code = self._hvac_mode_to_code[hvac_mode]
                await self._send_command(self._mode_command, mode_code)
    
    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        if not self._fan_mode_command or not self._reverse_fan_mode_mapping:
            return
        await self._set_mapped_command(
            self._fan_mode_command,
            fan_mode,
            self._reverse_fan_mode_mapping
        )
    
    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode."""
        if not self._swing_mode_command or not self._reverse_swing_mode_mapping:
            return
        await self._set_mapped_command(
            self._swing_mode_command,
            swing_mode,
            self._reverse_swing_mode_mapping
        )

