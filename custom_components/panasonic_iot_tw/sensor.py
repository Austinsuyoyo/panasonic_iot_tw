"""Sensor platform for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, Iterable, Optional, Callable, Set

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
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
    """Set up Panasonic sensor entities."""
    await PlatformSetupHelper.setup_platform(
        hass, config_entry, async_add_entities,
        "get_sensor_entities", "sensor"
    )


class PanasonicSensor(PanasonicEntity, SensorEntity):
    """Unified configurable sensor for all types."""

    def __init__(
        self,
        coordinator,
        device_key: str,
        device_data: Dict[str, Any],
        command_type: str,
        name: str,
        sensor_key: str,
        device_class: Optional[SensorDeviceClass] = None,
        state_class: Optional[SensorStateClass] = None,
        unit: Optional[str] = None,
        icon: Optional[str] = None,
        value_processor: Optional[Callable[[Any], Any]] = None,
        data_source: str = "status",
        extra_state_processor: Optional[Callable[[Any], Dict[str, Any]]] = None,
        translation_key: Optional[str] = None,
        gate_command: Optional[str] = None,
        gate_allowed: Optional[Iterable[int]] = None,
        **kwargs
    ):
        """Initialize the configurable sensor.

        Args:
            coordinator: Data update coordinator
            device_key: Key of device in coordinator data (device_id)
            device_data: Device information dictionary
            command_type: Command type for status lookup
            name: Display name for sensor (fallback when translation not available)
            sensor_key: Unique key for sensor
            device_class: Home Assistant device class
            state_class: Home Assistant state class
            unit: Unit of measurement
            icon: Icon for sensor
            value_processor: Function to process raw value
            data_source: Data source ("status", "energy", "co2", "door")
            extra_state_processor: Function to generate extra state attributes
            translation_key: Translation key for entity name
            gate_command: Command type whose value gates this sensor (optional)
            gate_allowed: Gate values for which this sensor reports a value
            **kwargs: Additional attributes to set on entity
        """
        # Call parent with common initialization
        super().__init__(
            coordinator, device_key, device_data,
            sensor_key, name, translation_key, icon, **kwargs
        )

        # Sensor-specific attributes
        self._command_type = command_type
        self._data_source = data_source
        self._value_processor = value_processor or (lambda x: x)  # Keep lambda for identity function
        self._extra_state_processor = extra_state_processor
        self._gate_command = gate_command
        self._gate_allowed: Set[int] = set(gate_allowed or ())

        # Set sensor-specific entity attributes
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_unit_of_measurement = unit

    def _get_raw_value(self, command_type: str = None) -> Any:
        """Get raw value from data source (override to support special data sources)."""
        try:
            # Handle special data sources (energy, CO2, door)
            if self._data_source in ["energy", "co2", "door"]:
                return self._get_special_data_value()

            # Default: use parent's implementation
            return super()._get_raw_value(command_type or self._command_type)
        except (KeyError, TypeError):
            return None
    
    def _get_special_data_value(self) -> Any:
        """Get value from special data sources (energy, CO2, door)."""
        try:
            # Get SmartApp instance from coordinator
            smart_app = getattr(self.coordinator, 'smart_app', None)
            if not smart_app:
                _LOGGER.debug("SmartApp not available for special data source: %s", self._data_source)
                return None
            
            # Get device GWID
            device_gwid = self._device_data.get("gwid")
            if not device_gwid:
                _LOGGER.warning("No GWID found for special sensor: %s", self._sensor_key)
                return None
            
            # Get data based on source type
            if self._data_source == "energy":
                data = smart_app.get_device_energy_data(device_gwid)
                if data:
                    return float(data.get("Total_kwh", 0))
                    
            elif self._data_source == "co2":
                data = smart_app.get_device_co2_data(device_gwid)
                if data:
                    return float(data.get("Total_kg", 0))
                    
            elif self._data_source == "door":
                data = smart_app.get_device_door_data(device_gwid)
                if data:
                    return int(data.get("Ref_OpenDoor_Total", 0))
            
            return None
            
        except (ValueError, TypeError, AttributeError) as e:
            _LOGGER.debug("Error getting special data value for %s: %s", self._sensor_key, e)
            return None
    
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # For special data sources, check if data is available
        if self._data_source in ["energy", "co2", "door"]:
            raw_value = self._get_special_data_value()
            return raw_value is not None
        
        # For normal sensors, check if device is available (live data)
        return (
            self.coordinator.last_update_success and
            self._current_device.get("available", False)
        )
    
    def _is_gate_open(self) -> bool:
        """Return True if the gating status allows this sensor to report a value."""
        if not self._gate_command:
            return True

        gate_value = self._get_status(self._gate_command)
        try:
            return int(gate_value) in self._gate_allowed
        except (ValueError, TypeError):
            _LOGGER.debug(
                "Gate %s unavailable for %s: %s",
                self._gate_command, self._attr_unique_id, gate_value
            )
            return False

    @property
    def native_value(self) -> Any:
        """Return the processed sensor value."""
        if not self._is_gate_open():
            return None

        raw_value = self._get_raw_value()
        return self._get_processed_value(raw_value, self._value_processor)

    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]:
        """Return additional state attributes."""
        if self._extra_state_processor and self._is_gate_open():
            raw_value = self._get_raw_value()
            return self._get_processed_value(raw_value, self._extra_state_processor)
        return None
