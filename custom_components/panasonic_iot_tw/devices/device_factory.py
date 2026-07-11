"""Device factory for creating device instances."""
import logging
import importlib
from typing import Dict, Any, Optional

from ..const import (
    DEVICE_TYPE_AC,
    DEVICE_TYPE_REFRIGERATOR,
    DEVICE_TYPE_WASHING_MACHINE,
    DEVICE_TYPE_DEHUMIDIFIER,
    DEVICE_TYPE_DRYER,
    DEVICE_TYPE_PURIFIER,
    DEVICE_TYPE_ERV,
    DEVICE_TYPE_SWITCH,
)
from ..base import BaseDevice

_LOGGER = logging.getLogger(__name__)


class DeviceFactory:
    """Factory class for creating device instances."""
    
    _device_classes = {}
    
    @classmethod
    def register_device_class(cls, device_type: int, device_class):
        """Register a device class for a device type."""
        cls._device_classes[device_type] = device_class
        _LOGGER.debug(f"Registered device class {device_class.__name__} for type {device_type}")
    
    @classmethod
    def create_device(cls, coordinator, device_index: int, device_data: Dict[str, Any]) -> Optional[BaseDevice]:
        """Create a device instance based on device type."""
        device_type = device_data.get("device_type")
        device_name = device_data.get("nickname", f"Device {device_index}")
        
        if device_type not in cls._device_classes:
            _LOGGER.warning(f"No device class registered for device type {device_type} ({device_name})")
            return None
        
        device_class = cls._device_classes[device_type]
        
        try:
            device = device_class(coordinator, device_index, device_data)
            _LOGGER.debug(f"Created {device_class.__name__} instance for {device_name}")
            return device
        except Exception as e:
            _LOGGER.error(f"Failed to create device instance for {device_name}: {e}")
            return None
    
    @classmethod
    def get_supported_device_types(cls) -> list:
        """Return list of supported device types."""
        return list(cls._device_classes.keys())


def register_all_devices():
    """Register all available device classes using data-driven approach."""
    # Device mappings: (device_type, module_name, class_name)
    device_mappings = [
        (DEVICE_TYPE_AC, "air_conditioner", "AirConditionerDevice"),
        (DEVICE_TYPE_REFRIGERATOR, "refrigerator", "RefrigeratorDevice"),
        (DEVICE_TYPE_WASHING_MACHINE, "washing_machine", "WashingMachineDevice"),
        (DEVICE_TYPE_DEHUMIDIFIER, "dehumidifier", "DehumidifierDevice"),
        (DEVICE_TYPE_DRYER, "dryer", "DryerDevice"),
        (DEVICE_TYPE_PURIFIER, "purifier", "PurifierDevice"),
        (DEVICE_TYPE_ERV, "erv", "ERVDevice"),
        (DEVICE_TYPE_SWITCH, "smart_switch", "SmartSwitchDevice"),
    ]
    
    registered_count = 0
    for device_type, module_name, class_name in device_mappings:
        try:
            # Dynamically import the module and get the class
            module_path = f"custom_components.panasonic_iot_tw.devices.{module_name}"
            module = importlib.import_module(module_path)
            device_class = getattr(module, class_name)
            DeviceFactory.register_device_class(device_type, device_class)
            registered_count += 1
        except (ImportError, AttributeError) as e:
            _LOGGER.warning(f"Failed to import {class_name} from {module_name}: {e}")
    
    _LOGGER.info(f"Registered {registered_count}/{len(device_mappings)} device types")