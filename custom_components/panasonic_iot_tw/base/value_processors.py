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


# ============================================================================
# Packed "phases still to run" words (laundry engineering register 0x34)
# ============================================================================
def create_pending_phase_processor(
    phases: Dict[int, str], finished: str = "finished"
) -> Callable[[Any], Optional[str]]:
    """Map a packed pending-phase word to the phase the programme runs now.

    The laundry engineering register (0x34) keeps one bit per phase of the
    programme that has *not finished yet*: the bit clears as that phase
    completes, so the word reaches 0 exactly when the programme ends. The
    phase in progress is therefore the highest bit still set — verified
    against 22k recorded polls, where the washer ran 112 -> 48 -> 16 -> 0
    and the dryer 12 -> 4 with the remaining time falling alongside.

    ``phases`` maps each bit mask to its slug, in any order.
    """
    ordered = sorted(phases.items(), reverse=True)

    def processor(value: Any) -> Optional[str]:
        try:
            packed = int(value)
        except (ValueError, TypeError):
            _LOGGER.debug("Invalid pending-phase value: %s", value)
            return None
        if packed == 0:
            return finished
        for mask, slug in ordered:
            if packed & mask:
                return slug
        return None

    return processor


def create_current_phase_matcher(
    phases: Dict[int, str], target: str
) -> Callable[[Any], bool]:
    """Return True only while ``target`` is the phase being run.

    Per-phase binary sensors used to test their own bit, which stays set for
    the whole programme and made every phase read as active at once. They now
    share the pending-phase decoding, so the phases are mutually exclusive.
    """
    pending = create_pending_phase_processor(phases)

    def processor(value: Any) -> bool:
        return pending(value) == target

    return processor


# ============================================================================
# Dispenser levels (laundry register 0x72)
# ============================================================================
# The dispenser word is the sum of the two amounts the app sends when a
# programme starts, so reading it back splits into the detergent amount in the
# high byte and the softener amount in the low nibble. Both are levels rather
# than volumes: the app's own picker offers 無 / 較少 / 標準 / 較多 and the
# detergent side is stored scaled by 256 (its standard setting reads 512, i.e.
# level 2). The app hides a tank's warning unless its level is non-zero, which
# is why a machine that never uses a slot keeps that warning byte at 0 forever.
def dispenser_detergent_level(value: Any) -> int:
    """Detergent level from the dispenser word, as the app reads it (0 = 無)."""
    try:
        packed = int(value)
    except (ValueError, TypeError):
        return 0
    return packed // 256 if packed < 1000 else 0


def dispenser_softener_level(value: Any) -> int:
    """Softener level from the dispenser word's low nibble (0 = 無)."""
    try:
        return int(value) % 16
    except (ValueError, TypeError):
        return 0


def dispenser_has_detergent(value: Any) -> bool:
    """True when the detergent slot is in use, so its warning means something."""
    return dispenser_detergent_level(value) != 0


def dispenser_has_softener(value: Any) -> bool:
    """True when the softener slot is in use, so its warning means something."""
    return dispenser_softener_level(value) != 0


def create_level_processor(
    level_of: Callable[[Any], int], levels: Dict[int, str]
) -> Callable[[Any], Optional[str]]:
    """Map a packed register to a named level through a level extractor."""
    def processor(value: Any) -> Optional[str]:
        return levels.get(level_of(value))
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


# The cloud answers 65535 for a register it has no value for. It also slipped
# into the refrigerator's status word for single polls (2026-09-23, 09-29)
# between ordinary readings of 30, so it is a "no data" marker, not a reading.
NO_DATA_REGISTER_VALUE = 65535


def raw_register_word(value: Any) -> int:
    """Return a raw register word, rejecting the cloud's no-data marker."""
    word = int(value)
    if word == NO_DATA_REGISTER_VALUE:
        raise ValueError("register returned the no-data marker")
    return word


def process_status_flag_bits(value: Any) -> Dict[str, Any]:
    """Break a packed status word into its individual bits.

    The meaning of each bit is still unknown, so they are published as-is:
    correlating a bit with an appliance event is what identifies it.
    """
    packed = raw_register_word(value)
    attrs: Dict[str, Any] = {
        "raw_value": packed,
        "binary": f"0b{packed:0{STATUS_FLAG_BIT_WIDTH}b}",
    }
    for bit in range(STATUS_FLAG_BIT_WIDTH):
        attrs[f"bit_{bit}"] = bool(packed & (1 << bit))
    return attrs
