"""Unified platform setup helper for reducing code duplication."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
        _LOGGER.debug("Setting up Panasonic %s platform...", platform_name)

        # Register all device classes
        register_all_devices()

        coordinator = config_entry.runtime_data

        entities = []
        if not coordinator.data:
            _LOGGER.warning("No coordinator data available for %s setup", platform_name)
            return

        for device_key, device_data in coordinator.data.items():
            device_type = device_data.get("device_type")
            device_name = device_data.get("nickname", "Unknown")

            _LOGGER.debug("Processing device %s: %s (type=%s)", device_key, device_name, device_type)

            # Create device instance using factory
            device = DeviceFactory.create_device(coordinator, device_key, device_data)
            if device:
                # Get entities from device using the specified getter method
                getter = getattr(device, entity_getter_name, None)
                if getter:
                    device_entities = getter(coordinator)
                    entities.extend(device_entities)
                    _LOGGER.debug("Created %s %s entities for %s", len(device_entities), platform_name, device_name)
            else:
                _LOGGER.warning("Failed to create device instance for type %s: %s", device_type, device_name)

        _LOGGER.debug("Adding %s %s entities to Home Assistant", len(entities), platform_name)
        async_add_entities(entities)
