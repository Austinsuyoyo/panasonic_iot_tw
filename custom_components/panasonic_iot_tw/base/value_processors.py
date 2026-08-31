"""Common value processing functions for all entities."""
import logging
from typing import Any, Dict, Callable, List, Optional

_LOGGER = logging.getLogger(__name__)


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
    """Process remote control allowance (0=not allowed, 1=allowed)."""
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
def create_status_mapping_processor(status_mapping: Dict[int, str]) -> Callable[[Any], Optional[str]]:
    """Create a status processor with mapping. Returns None for unmapped values."""
    def processor(value: Any) -> Optional[str]:
        status_int = int(value)
        slug = status_mapping.get(status_int)
        if slug is None:
            _LOGGER.debug("Unmapped status value: %s", status_int)
        return slug
    return processor


def create_options_processor(options_dict: Dict[int, str]) -> Callable[[Any], Optional[str]]:
    """Create a processor for select options mapping. Returns None for unmapped values."""
    def processor(value: Any) -> Optional[str]:
        try:
            option_key = int(value)
        except (ValueError, TypeError):
            _LOGGER.debug("Invalid option value: %s", value)
            return None
        slug = options_dict.get(option_key)
        if slug is None:
            _LOGGER.debug("Unmapped option value: %s", value)
        return slug
    return processor


def create_humidity_mapping_processor(humidity_mapping: Dict[int, int]) -> Callable[[Any], int]:
    """Create a processor for humidity mapping."""
    def processor(value: Any) -> int:
        humidity_index = int(value)
        return humidity_mapping.get(humidity_index, 50)
    return processor


def create_mode_processor(available_modes: Dict[int, str]) -> Callable[[Any], Optional[str]]:
    """Create a processor for mode values. Returns None for unmapped values."""
    def processor(value: Any) -> Optional[str]:
        mode_int = int(value)
        slug = available_modes.get(mode_int)
        if slug is None:
            _LOGGER.debug("Unmapped mode value: %s", mode_int)
        return slug
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



# Error Code Processors
def process_error_code(value: Any) -> Optional[str]:
    """Decode an appliance error register into its panel code.

    The register packs the code the machine shows on its own display: the
    high byte is the letter as ASCII and the low byte the number, so 0x550B
    is the drain fault "U11". Zero means no fault. Codes that do not fit
    that layout are reported as raw hex rather than guessed at.
    """
    code = int(value)
    if code == 0:
        return None

    letter, number = (code >> 8) & 0xFF, code & 0xFF
    if 0x41 <= letter <= 0x5A:
        return f"{chr(letter)}{number:02d}"
    return f"0x{code:04X}"


def process_error_code_attributes(value: Any) -> Dict[str, Any]:
    """Expose the undecoded register alongside the code."""
    return {"raw_value": int(value)}


# Registers seen so far need 16 bits: the refrigerator's door word reads
# 33320 (bit 15) and the laundry registers reach 1024 (bit 10).
STATUS_FLAG_BIT_WIDTH = 16


def process_status_flag_bits(value: Any) -> Dict[str, Any]:
    """Break a packed status word into its individual bits.

    The meaning of each bit is still unknown, so they are published as-is:
    correlating a bit with an appliance event is what identifies it.
    """
    packed = int(value)
    attrs: Dict[str, Any] = {
        "raw_value": packed,
        "binary": f"0b{packed:0{STATUS_FLAG_BIT_WIDTH}b}",
    }
    for bit in range(STATUS_FLAG_BIT_WIDTH):
        attrs[f"bit_{bit}"] = bool(packed & (1 << bit))
    return attrs
