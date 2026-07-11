"""Common value processing functions for all entities."""
from typing import Any, Dict, Callable, List


# ============================================================================
# Mapping Helper Class
# ============================================================================

class MappingHelper:
    """Helper for managing bidirectional value mappings."""
    
    def __init__(self, mapping: Dict[int, str]):
        """Initialize mapping helper with forward mapping.
        
        Args:
            mapping: Dictionary mapping integer keys to string values
        """
        self._forward = mapping
        self._reverse = {v: k for k, v in mapping.items()}
    
    def get_name(self, key: int, default: str = "未知") -> str:
        """Get string name from integer key.
        
        Args:
            key: Integer key
            default: Default value if key not found
            
        Returns:
            String name or default
        """
        return self._forward.get(key, f"{default} ({key})")
    
    def get_key(self, name: str, default: int = 0) -> int:
        """Get integer key from string name.
        
        Args:
            name: String name
            default: Default value if name not found
            
        Returns:
            Integer key or default
        """
        return self._reverse.get(name, default)
    
    def get_names(self) -> List[str]:
        """Get all available names."""
        return list(self._forward.values())
    
    def has_name(self, name: str) -> bool:
        """Check if name exists in mapping."""
        return name in self._reverse
    
    def has_key(self, key: int) -> bool:
        """Check if key exists in mapping."""
        return key in self._forward


# ============================================================================
# Boolean Processors
# ============================================================================
def safe_bool(value: Any) -> bool:
    """Safely convert value to boolean."""
    return bool(int(value))


def process_boolean(value: Any) -> bool:
    """Process simple boolean value."""
    return bool(int(value))


# Integer Processors
def safe_int(value: Any) -> int:
    """Safely convert value to integer."""
    return int(value)


def process_integer(value: Any) -> int:
    """Process integer value."""
    return int(value)


# Float Processors
def safe_float(value: Any) -> float:
    """Safely convert value to float."""
    return float(value)


def process_float(value: Any) -> float:
    """Process float value."""
    return float(value)


# Temperature Processors
def process_signed_temperature(value: Any) -> float:
    """Process signed temperature value (handles negative temperatures)."""
    temp_int = int(value)
    if temp_int > 128:
        temp_int = temp_int - 256
    return float(temp_int)


def process_temperature_command(value: float) -> int:
    """Convert temperature to device command (handles negative)."""
    device_value = int(value)
    if device_value < 0:
        device_value = device_value + 256
    return device_value


def process_climate_temperature(value: Any) -> float:
    """Process climate temperature (0.1°C units to Celsius)."""
    return float(value) / 10.0


def process_climate_temperature_command(value: float) -> int:
    """Process temperature command (Celsius to 0.1°C units)."""
    return int(value * 10)


def process_signed_climate_temperature(value: Any) -> float:
    """Process signed climate temperature with conversion."""
    temp_int = int(value)
    if temp_int > 128:
        temp_int = temp_int - 256
    return float(temp_int) / 10.0


def process_signed_climate_temperature_command(value: float) -> int:
    """Process signed temperature command with conversion."""
    device_value = int(value * 10)
    if device_value < 0:
        device_value = device_value + 256
    return device_value


# Command Processors
def process_command_boolean(value: bool) -> int:
    """Process boolean to command value (0/1)."""
    return 1 if value else 0


def process_integer_command(value: float) -> int:
    """Process float value to integer command."""
    return int(value)


# ============================================================================
# Binary Sensor Processors
# ============================================================================

def process_remote_control(value: Any) -> bool:
    """Process remote control allowance (0=不允許 1=允許)."""
    return bool(int(value))


def create_running_status_processor(running_codes: List[int]) -> Callable[[Any], bool]:
    """Create a processor for running status (washing/dryer machines).
    
    Args:
        running_codes: List of status codes that indicate running state
        
    Returns:
        Processor function
    """
    def processor(value: Any) -> bool:
        status_int = int(value)
        return status_int in running_codes
    return processor


# ============================================================================
# Number Processors
# ============================================================================

def process_float_number(value: Any) -> float:
    """Process simple float number value."""
    return float(value)


def process_integer_number(value: Any) -> float:
    """Process integer number value as float."""
    return float(int(value))


def process_signed_temperature_number(value: Any) -> float:
    """Process signed temperature value for number entities."""
    temp_int = int(value)
    if temp_int > 128:
        temp_int = temp_int - 256
    return float(temp_int)


# ============================================================================
# Switch Processors
# ============================================================================

def process_boolean_switch(value: Any) -> bool:
    """Process simple boolean switch value."""
    return bool(int(value))


# Factory Functions
def create_status_mapping_processor(status_mapping: Dict[int, str]) -> Callable[[Any], str]:
    """Create a status processor with mapping."""
    def processor(value: Any) -> str:
        status_int = int(value)
        return status_mapping.get(status_int, f"未知 ({status_int})")
    return processor


def create_options_processor(options_dict: Dict[int, str]) -> Callable[[Any], str]:
    """Create a processor for select options mapping."""
    def processor(value: Any) -> str:
        try:
            option_key = int(value)
            return options_dict.get(option_key, f"未知 ({value})")
        except (ValueError, TypeError):
            return f"無效 ({value})"
    return processor


def create_running_status_processor(running_codes: list) -> Callable[[Any], bool]:
    """Create a processor for running status (washing/dryer machines)."""
    def processor(value: Any) -> bool:
        status_int = int(value)
        return status_int in running_codes
    return processor


def create_humidity_mapping_processor(humidity_mapping: Dict[int, int]) -> Callable[[Any], int]:
    """Create a processor for humidity mapping."""
    def processor(value: Any) -> int:
        humidity_index = int(value)
        return humidity_mapping.get(humidity_index, 50)
    return processor


def create_mode_processor(available_modes: Dict[int, str]) -> Callable[[Any], str]:
    """Create a processor for mode values."""
    def processor(value: Any) -> str:
        mode_int = int(value)
        return available_modes.get(mode_int, "未知")
    return processor


# Time Formatters
def create_time_formatter(unit: str = "minutes") -> Callable[[Any], Dict[str, str]]:
    """Create a time formatter function."""
    def formatter(value: Any) -> Dict[str, str]:
        time_val = int(value)
        if time_val > 0:
            if unit == "minutes":
                hours = time_val // 60
                minutes = time_val % 60
                if hours > 0:
                    return {"formatted_time": f"{hours}小時{minutes}分鐘"}
                else:
                    return {"formatted_time": f"{minutes}分鐘"}
            else:
                return {"formatted_time": f"{time_val}小時"}
        else:
            return {"formatted_time": "0分鐘"}
    return formatter

