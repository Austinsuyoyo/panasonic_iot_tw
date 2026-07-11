"""Unified platform setup helper for reducing code duplication."""
import logging
from typing import Callable

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ..const import DOMAIN, DATA_COORDINATOR
from ..devices.device_factory import DeviceFactory, register_all_devices

_LOGGER = logging.getLogger(__name__)


class PlatformSetupHelper:
    """Unified platform setup logic for all entity types."""

    @staticmethod
    async def setup_platform(
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
        entity_getter_name: str,
        platform_name: str
    ) -> None:
        """
        Generic platform setup logic.

        Args:
            hass: Home Assistant instance
            config_entry: Config entry
            async_add_entities: Callback to add entities
            entity_getter_name: Method name to call on device (e.g., "get_sensor_entities")
            platform_name: Platform name for logging (e.g., "sensor")
        """
        _LOGGER.info(f"Setting up Panasonic {platform_name} platform...")

        # Register all device classes
        register_all_devices()

        coordinator = hass.data[DOMAIN][config_entry.entry_id][DATA_COORDINATOR]

        entities = []
        if not coordinator.data:
            _LOGGER.warning(f"No coordinator data available for {platform_name} setup")
            return

        for device_index, device_data in coordinator.data.items():
            device_type = device_data.get("device_type")
            device_name = device_data.get("nickname", "Unknown")

            _LOGGER.debug(f"Processing device {device_index}: {device_name} (type={device_type})")

            # Create device instance using factory
            device = DeviceFactory.create_device(coordinator, device_index, device_data)
            if device:
                # Get entities from device using the specified getter method
                getter = getattr(device, entity_getter_name, None)
                if getter:
                    device_entities = getter(coordinator)
                    entities.extend(device_entities)
                    _LOGGER.info(f"Created {len(device_entities)} {platform_name} entities for {device_name}")
            else:
                _LOGGER.warning(f"Failed to create device instance for type {device_type}: {device_name}")

        _LOGGER.info(f"Adding {len(entities)} {platform_name} entities to Home Assistant")
        async_add_entities(entities)
