"""Base entity class for all Panasonic entities."""
import logging
from typing import Any, Dict, Optional, Callable, Union

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from ..const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


class PanasonicEntity(CoordinatorEntity):
    """Unified base class for all Panasonic entities."""

    def __init__(
        self,
        coordinator,
        device_index: int,
        device_data: Dict[str, Any],
        entity_key: str,
        name: str,
        translation_key: Optional[str] = None,
        icon: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Panasonic entity.

        Args:
            coordinator: Data update coordinator
            device_index: Index of device in coordinator data
            device_data: Device information dictionary
            entity_key: Unique key suffix for this entity (e.g., "power", "temperature")
            name: Display name for entity (fallback when translation not available)
            translation_key: Translation key for entity name
            icon: Icon for entity
            **kwargs: Additional attributes to set on entity
        """
        super().__init__(coordinator)

        # Store device information
        self._device_index = device_index
        self._device_data = device_data
        self._device_id = device_data.get("device_id", "")

        # Setup entity naming
        self._setup_entity_name(name, translation_key)

        # Setup unique ID and device info
        self._attr_unique_id = f"{self._device_id}_{entity_key}"
        self._attr_device_info = self._build_device_info()

        # Set icon if provided
        if icon:
            self._attr_icon = icon

        # Apply any additional attributes
        self._apply_kwargs(kwargs)

    def _setup_entity_name(self, name: str, translation_key: Optional[str] = None):
        """Setup entity name using translation key or traditional naming."""
        if translation_key:
            # Use translation system for entity names
            self._attr_has_entity_name = True
            self._attr_translation_key = translation_key
        else:
            # Traditional naming with device nickname
            self._attr_name = f"{self._device_data.get('nickname', 'Panasonic Device')} {name}"

    def _build_device_info(self) -> DeviceInfo:
        """Build device information for Home Assistant."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=self._device_data.get("nickname", "Unknown Device"),
            manufacturer=MANUFACTURER,
            model=self._device_data.get("model", "Unknown Model"),
        )

    def _apply_kwargs(self, kwargs: Dict[str, Any]):
        """Apply additional keyword arguments as entity attributes.
        
        Sets attributes with _attr_ prefix. This allows overriding Home Assistant
        entity properties without conflicting with existing methods/properties.
        """
        for key, value in kwargs.items():
            attr_name = f"_attr_{key}"
            # Always set _attr_ prefixed attributes from kwargs
            # Home Assistant entity classes read from _attr_ attributes first
            setattr(self, attr_name, value)

    @property
    def available(self) -> bool:
        """Return if entity is available (can be overridden by subclasses)."""
        return (
            self.coordinator.last_update_success and
            self._device_data.get("available", False)
        )

    def _get_status(self, command_type: str) -> Any:
        """
        Get device status value for a specific command type.

        Args:
            command_type: The command type to look up (e.g., "0x00", "0x01")

        Returns:
            The status value for the command type, or None if not found
        """
        try:
            device_status = self.coordinator.data[self._device_index].get("status", {})
            return device_status.get(command_type)
        except (KeyError, TypeError):
            return None

    def _get_raw_value(self, command_type: str) -> Any:
        """
        Get raw value from device status (simple version, can be overridden).

        Args:
            command_type: The command type to look up (e.g., "0x00", "0x01")

        Returns:
            The raw value from device status, or None if not found

        Note:
            Subclasses can override this method for custom data sources
            (e.g., sensor.py handles special data sources like energy/CO2)
        """
        try:
            device_status = self.coordinator.data[self._device_index].get("status", {})
            return device_status.get(command_type)
        except (KeyError, TypeError):
            return None

    async def _send_command(self, command_type: str, value: Any) -> bool:
        """
        Send command to device through SmartApp.

        Args:
            command_type: The command type to send (e.g., "0x00", "0x01")
            value: The value to set for the command

        Returns:
            True if command was sent successfully, False otherwise
        """
        try:
            # Use the coordinator's SmartApp to send command
            smart_app = getattr(self.coordinator, "smart_app", None)
            if smart_app:
                success = await smart_app.set_device_command(
                    self._device_index, command_type, value
                )
                if success:
                    # Trigger a coordinator refresh to update the state
                    await self.coordinator.async_request_refresh()
                return success
            return False
        except Exception as e:
            _LOGGER.error(
                f"Failed to send command {command_type}={value} for {self._attr_unique_id}: {e}"
            )
            return False

    def _safe_process_value(
        self,
        raw_value: Any,
        processor: Callable[[Any], Any],
        default: Any = None
    ) -> Any:
        """
        Safely process a value with error handling.

        Args:
            raw_value: The raw value to process
            processor: Function to process the value
            default: Default value to return on error

        Returns:
            Processed value or default on error
        """
        if raw_value is None:
            return default
        try:
            return processor(raw_value)
        except (ValueError, TypeError) as e:
            _LOGGER.debug(
                f"Error processing value for {self._attr_unique_id}: {e}"
            )
            return default

    def _check_command_available(self, command_type: str) -> bool:
        """
        Check if a specific command type has data available.

        Args:
            command_type: The command type to check

        Returns:
            True if command data is available, False otherwise
        """
        return self._get_status(command_type) is not None

    def _check_readonly(self, operation: str = "modify") -> bool:
        """
        Check if entity is readonly and log warning if attempting to modify.

        Args:
            operation: Description of the operation being attempted

        Returns:
            True if entity is readonly, False otherwise
        """
        if getattr(self, '_readonly', False):
            _LOGGER.warning(
                f"Cannot {operation} readonly entity: {self._attr_name} "
                f"(entity_id: {self._attr_unique_id})"
            )
            return True
        return False

    def _get_processed_value(
        self,
        raw_value: Any,
        processor: Callable[[Any], Any],
        default: Any = None
    ) -> Any:
        """
        Process raw value with error handling.

        Args:
            raw_value: The raw value to process
            processor: Function to process the value
            default: Default value to return on error

        Returns:
            Processed value or default on error
        """
        if raw_value is not None:
            try:
                return processor(raw_value)
            except (ValueError, TypeError) as e:
                _LOGGER.debug(
                    f"Error processing value for {self._attr_unique_id}: {e}"
                )
                return default
        return default

    def _available_with_command(self, command_type: str) -> bool:
        """
        Check if entity is available and command data exists.

        Args:
            command_type: The command type to check

        Returns:
            True if entity is available and command has data
        """
        base_available = (
            self.coordinator.last_update_success and
            self._device_data.get("available", False)
        )
        return base_available and self._check_command_available(command_type)

    def _get_mapped_value(
        self,
        command_type: str,
        mapping: Dict[int, str],
        default: str = "未知"
    ) -> Optional[str]:
        """
        Get mapped string value from command.
        
        Args:
            command_type: Command type to query
            mapping: Mapping dictionary (int -> str)
            default: Default value if key not found
            
        Returns:
            Mapped string value or None
        """
        raw_value = self._get_raw_value(command_type)
        if raw_value is not None:
            try:
                key = int(raw_value)
                return mapping.get(key, f"{default} ({key})")
            except (ValueError, TypeError) as e:
                _LOGGER.debug(
                    f"Error mapping value for {self._attr_unique_id}: {e}"
                )
                return None
        return None

    async def _set_mapped_command(
        self,
        command_type: str,
        target_value: str,
        reverse_mapping: Dict[str, int]
    ) -> bool:
        """
        Set command using reverse mapping.
        
        Args:
            command_type: Command type to set
            target_value: Target value name
            reverse_mapping: Reverse mapping (str -> int)
            
        Returns:
            True if successful
        """
        if target_value in reverse_mapping:
            device_value = reverse_mapping[target_value]
            return await self._send_command(command_type, device_value)
        else:
            _LOGGER.warning(
                f"Invalid value '{target_value}' for {self._attr_unique_id}. "
                f"Valid values: {list(reverse_mapping.keys())}"
            )
            return False

    def _get_conditional_processed_value(
        self,
        command_type: Optional[str],
        processor: Callable[[Any], Any],
        default: Any = None
    ) -> Any:
        """
        Get processed value with optional command check.
        
        Args:
            command_type: Command type (can be None)
            processor: Processing function
            default: Default value
            
        Returns:
            Processed value or default
        """
        if not command_type:
            return default
        raw_value = self._get_raw_value(command_type)
        return self._get_processed_value(raw_value, processor, default)

    def _create_reverse_mapping(self, forward_mapping: Dict[int, str]) -> Dict[str, int]:
        """
        Create reverse mapping from forward mapping.
        
        Args:
            forward_mapping: Dictionary mapping int keys to string values
            
        Returns:
            Dictionary mapping string values to int keys
        """
        return {v: k for k, v in forward_mapping.items()}
