"""Status reader base class - unified device status reading logic"""
import logging
from typing import Any, Optional, Callable, Union

# Use local definition if unable to import Home Assistant
try:
    from homeassistant.const import STATE_UNAVAILABLE
except ImportError:
    STATE_UNAVAILABLE = "unavailable"

_LOGGER = logging.getLogger(__name__)


class StatusReader:
    """Unified status reading base class to reduce code duplication"""
    
    def __init__(self, coordinator, index: int, label: str):
        self.coordinator = coordinator
        self.index = index
        self.label = label
    
    def get_status_value(
        self, 
        command_type: str, 
        default: Any = None,
        transform: Optional[Callable[[Any], Any]] = None,
        validate: Optional[Callable[[Any], bool]] = None
    ) -> Any:
        """
        Unified status value retrieval method
        
        Args:
            command_type: Command type (e.g. "0x00")
            default: Default value
            transform: Value transformation function
            validate: Validation function
            
        Returns:
            Processed status value
        """
        try:
            status = self.coordinator.data[self.index]["status"]
            raw_value = status.get(command_type, default)
            
            if raw_value is None:
                return STATE_UNAVAILABLE
            
            # Validate value
            if validate and not validate(raw_value):
                _LOGGER.warning(f"[{self.label}] Invalid value for {command_type}: {raw_value}")
                return STATE_UNAVAILABLE
            
            # Convert value
            if transform:
                try:
                    processed_value = transform(raw_value)
                except (ValueError, TypeError) as e:
                    _LOGGER.warning(f"[{self.label}] Transform error for {command_type}: {e}")
                    return STATE_UNAVAILABLE
            else:
                processed_value = raw_value
            return processed_value
            
        except (KeyError, IndexError) as e:
            _LOGGER.exception(f"[{self.label}] Error getting status for {command_type}: {e}")
            return STATE_UNAVAILABLE
    
    def get_boolean_status(self, command_type: str, default: bool = False) -> bool:
        """Get boolean status value"""
        def bool_transform(value):
            if isinstance(value, str):
                return bool(int(value))
            return bool(value)
        
        return self.get_status_value(command_type, default, bool_transform)
    
    def get_int_status(self, command_type: str, default: int = 0) -> Union[int, str]:
        """Get integer status value"""
        def int_transform(value):
            return int(float(value))
        
        return self.get_status_value(command_type, default, int_transform)
    
    def get_float_status(self, command_type: str, default: float = 0.0) -> Union[float, str]:
        """Get float status value"""
        def float_transform(value):
            return float(value)
        
        return self.get_status_value(command_type, default, float_transform)
    
    def get_temperature_status(self, command_type: str) -> Union[int, str]:
        """Get temperature status value (handle signed/unsigned conversion)"""
        def temp_transform(value):
            temp = int(value)
            # Handle signed temperature conversion
            return temp if temp < 128 else temp - 256
        
        return self.get_status_value(command_type, 0, temp_transform)
    
    def is_device_available(self, power_command: str = "0x00") -> bool:
        """Check if device is available"""
        try:
            status = self.coordinator.data[self.index]["status"]
            return status.get(power_command) is not None
        except (KeyError, IndexError):
            return False