"""Base device class for all Panasonic IoT TW devices."""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .status_reader import StatusReader

_LOGGER = logging.getLogger(__name__)


class BaseDevice(StatusReader, ABC):
    """Base class for all Panasonic devices."""
    
    def __init__(self, coordinator, device_index: int, device_data: Dict[str, Any]):
        """Initialize base device."""
        super().__init__(
            coordinator,
            device_index,
            device_data.get("nickname", f"Device {device_index}")
        )
        self._device_data = device_data
        self._device_type = device_data.get("device_type")
        self._model = device_data.get("model", "Unknown")
        self._device_id = device_data.get("device_id", f"device_{device_index}")
    
    @property
    def device_data(self) -> Dict[str, Any]:
        """Return device data with dynamic availability check.

        Subclasses can override this to implement custom availability logic.
        """
        return self._device_data.copy()

    @device_data.setter
    def device_data(self, value: Dict[str, Any]):
        """Set device data."""
        self._device_data = value

    def is_device_available(self) -> bool:
        """Check if device is available based on current status.

        Base implementation returns the static availability flag.
        Subclasses can override this for dynamic availability checking.
        """
        return self._device_data.get("available", False)
    
    @property
    def device_type(self) -> int:
        """Return device type."""
        return self._device_type
    
    @property
    def model(self) -> str:
        """Return device model."""
        return self._model
    
    @property
    def device_id(self) -> str:
        """Return device ID."""
        return self._device_id
    
    def get_device_info(self) -> Dict[str, Any]:
        """Return device information for Home Assistant."""
        return {
            "identifiers": {("panasonic_iot_tw", self._device_id)},
            "name": self._device_data.get("nickname", f"Panasonic {self._model}"),
            "manufacturer": "Panasonic",
            "model": self._model,
            "sw_version": self._device_data.get("version"),
        }
    
    # Entity creation methods - devices should implement these as needed
    def get_sensor_entities(self, coordinator) -> List:
        """Return sensor entities for this device."""
        return []
    
    def get_binary_sensor_entities(self, coordinator) -> List:
        """Return binary sensor entities for this device."""
        return []
    
    def get_switch_entities(self, coordinator) -> List:
        """Return switch entities for this device."""
        return []
    
    def get_select_entities(self, coordinator) -> List:
        """Return select entities for this device."""
        return []
    
    def get_number_entities(self, coordinator) -> List:
        """Return number entities for this device."""
        return []
    
    def get_climate_entities(self, coordinator) -> List:
        """Return climate entities for this device."""
        return []
    
    def get_humidifier_entities(self, coordinator) -> List:
        """Return humidifier entities for this device."""
        return []
    
    def get_button_entities(self, coordinator) -> List:
        """Return button entities for this device."""
        return []

    # Entity creation helper methods
    def _create_sensor(self, coordinator, **kwargs):
        """Helper to create sensor entity with common parameters."""
        from ..sensor import PanasonicSensor
        return PanasonicSensor(
            coordinator, self.index, self.device_data,
            **kwargs
        )

    def _create_binary_sensor(self, coordinator, **kwargs):
        """Helper to create binary sensor entity with common parameters."""
        from ..binary_sensor import PanasonicBinarySensor
        return PanasonicBinarySensor(
            coordinator, self.index, self.device_data,
            **kwargs
        )

    def _create_switch(self, coordinator, **kwargs):
        """Helper to create switch entity with common parameters."""
        from ..switch import PanasonicSwitch
        return PanasonicSwitch(
            coordinator, self.index, self.device_data,
            **kwargs
        )

    def _create_select(self, coordinator, **kwargs):
        """Helper to create select entity with common parameters."""
        from ..select import PanasonicSelect
        return PanasonicSelect(
            coordinator, self.index, self.device_data,
            **kwargs
        )

    def _create_number(self, coordinator, **kwargs):
        """Helper to create number entity with common parameters."""
        from ..number import PanasonicNumber
        return PanasonicNumber(
            coordinator, self.index, self.device_data,
            **kwargs
        )

    def _create_button(self, coordinator, **kwargs):
        """Helper to create button entity with common parameters."""
        from ..button import PanasonicButton
        return PanasonicButton(
            coordinator, self.index, self.device_data,
            **kwargs
        )

    def _create_climate(self, coordinator, **kwargs):
        """Helper to create climate entity with common parameters."""
        from ..climate import PanasonicClimate
        return PanasonicClimate(
            coordinator, self.index, self.device_data,
            **kwargs
        )

    def _create_humidifier(self, coordinator, **kwargs):
        """Helper to create humidifier entity with common parameters."""
        from ..humidifier import PanasonicHumidifier
        return PanasonicHumidifier(
            coordinator, self.index, self.device_data,
            **kwargs
        )

