"""Constants for Panasonic IoT TW integration."""

from homeassistant.components.climate import HVACMode

# ============================================================================
# Integration Configuration
# ============================================================================
DOMAIN = "panasonic_iot_tw"
PLATFORMS = [
    "climate",
    "sensor", 
    "binary_sensor",
    "switch",
    "select",
    "number",
    "humidifier",
    "button",
]
MANUFACTURER = "Panasonic"
DEFAULT_NAME = "Panasonic IoT TW"

# ============================================================================
# Device Types
# ============================================================================
DEVICE_TYPE_AC = 1
DEVICE_TYPE_REFRIGERATOR = 2
DEVICE_TYPE_WASHING_MACHINE = 3
DEVICE_TYPE_DEHUMIDIFIER = 4
DEVICE_TYPE_DRYER = 6
DEVICE_TYPE_PURIFIER = 8
DEVICE_TYPE_ERV = 14
DEVICE_TYPE_SWITCH = 17

# ============================================================================
# Configuration
# ============================================================================
CONF_PROXY = "proxy"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 180

# ============================================================================
# Device Status Codes
# ============================================================================
DEVICE_STATUS_CODES = {
    DEVICE_TYPE_AC: [
        ("0x00", True),   # AC power status
        ("0x01", True),   # AC operation mode
        ("0x02", True),   # AC fan level
        ("0x03", True),   # AC target temperature
        ("0x04", True),   # AC current temperature
        ("0x05", True),   # AC sleep mode
        ("0x08", True),   # AC nanoeX
        ("0x0B", True),   # AC on timer
        ("0x0C", True),   # AC off timer
        ("0x0F", True),   # AC fan position (horizontal)
        ("0x11", True),   # AC fan position (vertical)
        ("0x17", True),   # AC mold prevention
        ("0x18", True),   # AC self clean
        ("0x19", True),   # AC motion detection
        ("0x1A", True),   # AC turbo mode
        ("0x1B", True),   # AC ECONAVI
        ("0x1E", True),   # AC buzzer
        ("0x1F", True),   # AC indicator light
        ("0x21", True),   # AC outdoor temperature
        ("0x37", True),   # AC PM2.5
    ],
    DEVICE_TYPE_REFRIGERATOR: [
        ("0x00", True),   # Freezer temperature setting (weak/medium/strong)
        ("0x01", True),   # Fridge temperature setting (weak/medium/strong)
        ("0x02", False),  # Unknown / Reserved
        ("0x03", True),   # Freezer temperature display (-40~40 degrees)
        ("0x04", False),  # Unknown / Reserved
        ("0x05", True),   # Fridge temperature display (-39~40 degrees)
        ("0x06", False),  # Unknown / Reserved
        ("0x07", False),  # Unknown / Reserved
        ("0x08", False),  # Unknown / Reserved
        ("0x09", False),  # Unknown / Reserved
        ("0x0A", False),  # Unknown / Reserved
        ("0x0B", False),  # Unknown / Reserved
        ("0x0C", True),   # ECO setting (normal/active)
        ("0x0D", False),  # Unknown / Reserved
        ("0x0E", False),  # Unknown / Reserved
        ("0x0F", False),  # Unknown / Reserved
        ("0x10", False),  # Unknown / Reserved
        ("0x11", False),  # Unknown / Reserved
        ("0x12", False),  # Unknown / Reserved
        ("0x13", False),  # Unknown / Reserved not 65535
        ("0x14", False),  # Unknown / Reserved
        ("0x15", False),  # Unknown / Reserved
        ("0x16", False),  # Unknown / Reserved
        ("0x17", False),  # Unknown / Reserved
        ("0x18", False),  # Unknown / Reserved
        ("0x19", False),  # Unknown / Reserved
        ("0x1A", False),  # Unknown / Reserved
        ("0x1B", False),  # Unknown / Reserved
        ("0x1C", False),  # Unknown / Reserved
        ("0x1D", False),  # Unknown / Reserved
        ("0x1E", False),  # Unknown / Reserved
        ("0x1F", False),  # Unknown / Reserved
        ("0x20", False),  # Unknown / Reserved
        ("0x21", False),  # Unknown / Reserved
        ("0x22", False),  # Unknown / Reserved
        ("0x23", False),  # Unknown / Reserved
        ("0x24", False),  # Unknown / Reserved
        ("0x25", False),  # Unknown / Reserved
        ("0x26", False),  # Unknown / Reserved
        ("0x27", False),  # Unknown / Reserved
        ("0x28", False),  # Unknown / Reserved
        ("0x29", False),  # Unknown / Reserved
        ("0x2A", False),  # Unknown / Reserved
        ("0x2B", False),  # Unknown / Reserved
        ("0x2C", False),  # Unknown / Reserved
        ("0x2D", False),  # Unknown / Reserved
        ("0x2E", False),  # Unknown / Reserved
        ("0x2F", False),  # Unknown / Reserved
        ("0x30", False),  # Unknown / Reserved
        ("0x31", False),  # Unknown / Reserved
        ("0x32", False),  # Unknown / Reserved
        ("0x33", False),  # Unknown / Reserved
        ("0x34", False),  # Unknown / Reserved
        ("0x35", False),  # Unknown / Reserved
        ("0x36", False),  # Unknown / Reserved
        ("0x37", False),  # Unknown / Reserved
        ("0x38", False),  # Unknown / Reserved
        ("0x39", False),  # Unknown / Reserved
        ("0x3A", False),  # Unknown / Reserved
        ("0x3B", False),  # Unknown / Reserved
        ("0x3C", False),  # Unknown / Reserved
        ("0x3D", False),  # Unknown / Reserved
        ("0x3E", False),  # Unknown / Reserved
        ("0x3F", False),  # Unknown / Reserved
        ("0x40", False),  # Unknown / Reserved
        ("0x41", False),  # Unknown / Reserved
        ("0x42", False),  # Unknown / Reserved
        ("0x43", False),  # Unknown / Reserved
        ("0x44", False),  # Unknown / Reserved
        ("0x45", False),  # Unknown / Reserved
        ("0x46", False),  # Unknown / Reserved
        ("0x47", False),  # Unknown / Reserved
        ("0x48", False),  # Unknown / Reserved
        ("0x49", False),  # Unknown / Reserved
        ("0x4A", False),  # Unknown / Reserved
        ("0x4B", False),  # Unknown / Reserved
        ("0x4C", False),  # Unknown / Reserved
        ("0x4D", False),  # Unknown / Reserved
        ("0x4E", False),  # Unknown / Reserved
        ("0x4F", False),  # Unknown / Reserved
        ("0x50", True),   # Defrost setting (normal/defrosting)
        ("0x51", True),   # Packed status bits, meaning not yet decoded; logged for study
        ("0x52", True),   # Ice-making stop (stopped/active)
        ("0x53", True),   # Quick ice-making (stopped/active)
        ("0x54", False),  # Unknown / Reserved
        ("0x55", False),  # Unknown / Reserved
        ("0x56", True),   # Fresh quick-freeze (normal/cooling/quick-cool/quick-freeze) value/256=mode value%256=minutes
        ("0x57", True),   # Partial-freeze compartment temperature setting (weak/medium/strong)
        ("0x58", True),   # Partial-freeze temperature display (-39~40 degrees)
        ("0x59", False),  # Unknown / Reserved
        ("0x5A", True),   # Winter mode (inactive/active/available)
        ("0x5B", True),   # Shopping mode (inactive/active/available)
        ("0x5C", True),   # Away mode (inactive/active/available)
        ("0x5D", False),  # Unknown / Reserved
        ("0x5E", False),  # Unknown / Reserved
        ("0x5F", False),  # Unknown / Reserved
        ("0x60", False),  # Unknown / Reserved
        ("0x61", True),   # nanoe (normal/active)
        ("0x62", False),  # Unknown / Reserved
        ("0x63", False),  # Unknown / Reserved
        ("0x64", False),  # Unknown / Reserved not 65535
        ("0x65", False),  # Unknown / Reserved not 65535
        ("0x66", True),   # Door status: bit15 (0x8000) = any door open; lower bits purpose unknown
        ("0x67", False),  # Unknown / Reserved
        ("0x68", False),  # Unknown / Reserved not 65535
        ("0x69", False),  # Unknown / Reserved not 65535
        ("0x6A", False),  # Unknown / Reserved
        ("0x6B", False),  # Unknown / Reserved
        ("0x6C", False),  # Unknown / Reserved
        ("0x6D", False),  # Unknown / Reserved
        ("0x6E", False),  # Unknown / Reserved
        ("0x6F", False),  # Unknown / Reserved
        ("0x70", False),  # Unknown / Reserved
        ("0x71", False),  # Unknown / Reserved
        ("0x72", False),  # Unknown / Reserved
        ("0x73", False),  # Unknown / Reserved
        ("0x74", False),  # Unknown / Reserved
        ("0x75", False),  # Unknown / Reserved
        ("0x76", False),  # Unknown / Reserved
        ("0x77", False),  # Unknown / Reserved
        ("0x78", False),  # Unknown / Reserved
        ("0x79", False),  # Unknown / Reserved
        ("0x7A", False),  # Unknown / Reserved
        ("0x7B", False),  # Unknown / Reserved
        ("0x7C", False),  # Unknown / Reserved
        ("0x7D", False),  # Unknown / Reserved
        ("0x7E", False),  # Unknown / Reserved
        ("0x7F", False),  # Unknown / Reserved
    ],
    DEVICE_TYPE_WASHING_MACHINE: [
        ("0x01", True),   # Unknown / Reserved
        ("0x03", False),  # Unknown / Reserved
        ("0x04", False),  # Unknown / Reserved
        ("0x05", False),  # Unknown / Reserved
        ("0x0A", False),  # Unknown / Reserved
        ("0x13", True),   # Washing remaining time (Min=0 Max=599 minutes)
        ("0x15", True),   # Schedule remaining time (Min=0 Max=24 hours)
        ("0x19", True),   # Error code (0=normal; high byte=panel letter, low byte=number)
        ("0x34", True),   # Engineering info (bitwise): bit7=prewash(128), bit6=wash(64), bit5=rinse(32), bit4=spin(16)
        ("0x40", False),  # Unknown / Reserved
        ("0x44", False),  # Unknown / Reserved
        ("0x45", False),  # Unknown / Reserved
        ("0x46", False),  # Unknown / Reserved
        ("0x48", False),  # Unknown / Reserved
        ("0x4A", False),  # Unknown / Reserved
        ("0x4B", False),  # Unknown / Reserved
        ("0x4E", False),  # Unknown / Reserved
        ("0x50", True),   # Operation status: 0-not displayed 1-standby 2-running 3-reserved 4-reserved 5-finished 8-error
        ("0x55", True),   # Cycle message (see WASHING_MACHINE_AVAILABLE_CYCLES for detailed cycle mapping)
        ("0x5A", False),  # Unknown / Reserved
        ("0x5B", False),  # Unknown / Reserved
        ("0x5C", False),  # Unknown / Reserved
        ("0x64", True),   # Engineering info (bitwise): bit10=prewash(1024), bit6=wash(64), bit5=rinse(32), bit4=spin(16)
        ("0x69", False),  # Unknown / Reserved
        ("0x71", True),   # Unknown / Reserved
        ("0x72", True),   # Unknown / Reserved
        ("0x73", True),   # Unknown / Reserved
        ("0x74", True),   # Whether remote idle is allowed 0=not allowed 1=allowed
        ("0x75", True),   # Unknown / Reserved
        ("0x79", False),  # Unknown / Reserved
    ],
    DEVICE_TYPE_DEHUMIDIFIER: [
        ("0x00", True),   # Dehumidifier power status
        ("0x01", True),   # Dehumidifier operation mode
        ("0x02", True),   # Dehumidifier off timer
        ("0x04", True),   # Dehumidifier target humidity
        ("0x07", True),   # Dehumidifier humidity sensor
        ("0x09", True),   # Dehumidifier fan direction
        ("0x0A", True),   # Dehumidifier tank status
        ("0x0D", True),   # Dehumidifier nanoe
        ("0x0E", True),   # Dehumidifier fan mode
        ("0x18", True),   # Dehumidifier buzzer
        ("0x50", True),   # Dehumidifier unknown status
        ("0x53", True),   # Dehumidifier PM2.5
        ("0x55", True),   # Dehumidifier on timer
        ("0x56", True),   # Dehumidifier PM1.0
    ],
    DEVICE_TYPE_DRYER: [
        ("0x01", True),   # Unknown / Reserved
        ("0x02", False),  # Unknown / Reserved
        ("0x03", False),  # Unknown / Reserved
        ("0x04", False),  # Unknown / Reserved
        ("0x05", True),   # Drying remaining time (Min=0 Max=599 remaining minutes)
        ("0x0A", True),   # Panel error code (0=normal; high byte=ASCII letter, low byte=number)
        ("0x13", False),  # Unknown / Reserved
        ("0x15", True),   # Schedule remaining time (Min=0 Max=24 hours)
        ("0x19", False),  # Not used by the dryer; error code is at 0x0A (verified by testing)
        ("0x34", True),   # Engineering info (bitwise): bit3=drying(8), bit2=air-flow(4), bit1=soft-cooling(2)
        ("0x40", False),  # Unknown / Reserved
        ("0x44", False),  # Unknown / Reserved
        ("0x45", False),  # Unknown / Reserved
        ("0x46", False),  # Unknown / Reserved
        ("0x48", False),  # Unknown / Reserved
        ("0x4A", False),  # Unknown / Reserved
        ("0x4B", False),  # Unknown / Reserved
        ("0x4E", False),  # Unknown / Reserved
        ("0x50", True),   # Operation status: 0-not displayed 1-standby 2-running 3-reserved 4-reserved 5-finished 8-error
        ("0x55", True),   # Cycle message (see DRYER_AVAILABLE_CYCLES for detailed cycle mapping)
        ("0x5A", False),  # Unknown / Reserved
        ("0x5B", False),  # Unknown / Reserved
        ("0x5C", False),  # Unknown / Reserved
        ("0x64", True),   # Engineering info (bitwise): bit3=drying(8), bit2=air-flow(4), bit1=soft-cooling(2)
        ("0x69", False),  # Unknown / Reserved
        ("0x71", True),   # Unknown / Reserved
        ("0x72", True),   # Unknown / Reserved
        ("0x73", True),   # Unknown / Reserved
        ("0x74", True),   # Whether remote idle is allowed 0=not allowed 1=allowed
        ("0x75", True),   # Unknown / Reserved
        ("0x79", False),  # Unknown / Reserved
    ],
    DEVICE_TYPE_PURIFIER: [
        ("0x00", True),   # Purifier power status
        ("0x01", True),   # Purifier fan level
        ("0x07", True),   # Purifier nanoeX
        ("0x50", True),   # Purifier PM 2.5
    ],
    DEVICE_TYPE_ERV: [
        ("0x00", True),   # ERV power status
        ("0x15", True),   # ERV operation mode
        ("0x56", True),   # ERV fan level
    ],
    DEVICE_TYPE_SWITCH: [
        ("0x70", True),   # Switch power status
    ],
}

# ============================================================================
# Climate Constants
# ============================================================================
CLIMATE_AVAILABLE_MODE = [
    {"key": HVACMode.OFF, "mappingCode": -1},
    {"key": HVACMode.COOL, "mappingCode": 0},
    {"key": HVACMode.DRY, "mappingCode": 1},
    {"key": HVACMode.FAN_ONLY, "mappingCode": 2},
    {"key": HVACMode.AUTO, "mappingCode": 3},
    {"key": HVACMode.HEAT, "mappingCode": 4},
]

CLIMATE_AVAILABLE_PRESET = {
    0: "Cool",
    1: "Dehumidify",
    2: "Fan",
    3: "Auto",
    4: "Heat"
}

CLIMATE_AVAILABLE_SWING_MODE = {
    0: "Auto",
    1: "0°",
    2: "20°",
    3: "45°",
    4: "70°",
    5: "90°",
}

CLIMATE_AVAILABLE_FAN_MODE = {
    0: "Auto",
    1: "20%",
    2: "40%",
    3: "60%",
    4: "80%",
    5: "100%",
}

CLIMATE_MINIMUM_TEMPERATURE = 16
CLIMATE_MAXIMUM_TEMPERATURE = 30
CLIMATE_TEMPERATURE_STEP = 1.0
CLIMATE_ON_TIMER_MIN = 0
CLIMATE_ON_TIMER_MAX = 1440
CLIMATE_OFF_TIMER_MIN = 0
CLIMATE_OFF_TIMER_MAX = 1440

# ============================================================================
# Dehumidifier Constants
# ============================================================================
DEHUMIDIFIER_MAX_HUMD = 70
DEHUMIDIFIER_MIN_HUMD = 40
DEHUMIDIFIER_AVAILABLE_HUMIDITY = {
    0: 40, 1: 45, 2: 50, 3: 55, 4: 60, 5: 65, 6: 70
}
DEHUMIDIFIER_ON_TIMER_MIN = 0
DEHUMIDIFIER_ON_TIMER_MAX = 12
DEHUMIDIFIER_OFF_TIMER_MIN = 0
DEHUMIDIFIER_OFF_TIMER_MAX = 12

# ============================================================================
# Dryer Constants
# ============================================================================
DRYER_AVAILABLE_STATUS = {
    0: "not_displayed",
    1: "standby",
    2: "running",
    3: "reserved",
    4: "reserved",
    5: "finished",
    8: "error"
}

DRYER_AVAILABLE_CYCLES = {
    0: "cotton_linen",
    13: "large_items",
    18: "custom",
    52: "premium_clothing",
    64: "wool",
    65: "sportswear",
    66: "down_jacket",
    67: "antibacterial_dry",
    70: "nanoex_antibacterial",
    71: "nanoex_deodorize",
    72: "nanoex_dust_mite",
    73: "nanoex_dewrinkle",
    74: "nanoex_softening",
    75: "nanoex_fur_care",
    76: "quick_dry",
    77: "baby_clothes",
    78: "thin_quilt",
    79: "synthetic_fiber",
    80: "shirts",
    81: "mixed",
    82: "functional_wear",
    83: "denim",
    84: "bath_towel",
    85: "cool_air_refresh",
    86: "work_school_uniform",
    87: "warm_air"
}

# ============================================================================
# Washing Machine Constants
# ============================================================================
WASHING_MACHINE_AVAILABLE_CYCLES = {
    0: "standard",
    8: "soak",
    10: "quick_wash",
    11: "tub_clean",
    13: "large_items",
    15: "dust_mite_removal",
    18: "custom",
    52: "premium_clothing",
    64: "wool",
    65: "sportswear",
    66: "down_jacket",
    67: "high_temp_antibacterial",
    68: "eco_wash",
    69: "spin",
    79: "synthetic_fiber",
    80: "shirts",
    81: "mixed",
    83: "denim"
}

WASHING_MACHINE_AVAILABLE_STATUS = {
    0: "not_displayed",
    1: "standby",
    2: "running",
    3: "reserved",
    4: "reserved",
    5: "finished",
    8: "error"
}

# ============================================================================
# Refrigerator Constants
# ============================================================================
REFRIGERATOR_TEMPERATURE_SETTINGS = {
    0: "low",
    2: "medium",
    4: "high"
}

# Fresh freezing compartment mode (register 0x56)
REFRIGERATOR_FRESH_FREEZING_MODES = {
    0: "normal",
    1: "cooling",
    2: "quick_cool",
    3: "quick_freeze"
}

# Activation state shared by winter/shopping/vacation modes (0x5A/0x5B/0x5C)
REFRIGERATOR_ACTIVATION_MODES = {
    0: "inactive",
    1: "active",
    2: "available"
}

# ============================================================================
# Special Sensors
# ============================================================================
# Device types that support energy/CO2/door sensors
SPECIAL_SENSOR_SUPPORTED_DEVICES = {DEVICE_TYPE_REFRIGERATOR}
