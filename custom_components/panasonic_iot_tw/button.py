"""Button platform for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, Optional, Callable

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .base import PanasonicEntity, PlatformSetupHelper

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Panasonic button entities."""
    await PlatformSetupHelper.setup_platform(
        hass, config_entry, async_add_entities,
        "get_button_entities", "button"
    )

class PanasonicButton(PanasonicEntity, ButtonEntity):
    """Unified configurable button for all types."""
    
    def __init__(
        self,
        coordinator,
        device_index: int,
        device_data: Dict[str, Any],
        command_type: str,
        name: str,
        button_key: str,
        icon: Optional[str] = None,
        command_value: Any = 1,
        command_processor: Optional[Callable[[Any], Any]] = None,
        press_action: Optional[Callable] = None,
        translation_key: Optional[str] = None,
        **kwargs
    ):
        """Initialize the configurable button entity.
        
        Args:
            coordinator: Data update coordinator
            device_index: Index of device in coordinator data
            device_data: Device information dictionary
            command_type: Command type for button press
            name: Display name for button (fallback when translation not available)
            button_key: Unique key for button
            icon: Icon for button
            command_value: Value to send when button is pressed
            command_processor: Function to process command value
            press_action: Custom action function for button press
            translation_key: Translation key for entity name
            **kwargs: Additional attributes to set on entity
        """
        super().__init__(
            coordinator, device_index, device_data,
            button_key, name, translation_key, icon, **kwargs
        )

        self._command_type = command_type
        self._command_value = command_value
        self._command_processor = command_processor or (lambda x: x)
        self._press_action = press_action
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get current device status."""
        return self.coordinator.data[self._device_index].get("status", {})
    
    def get_smart_app(self):
        """Get SmartApp instance from coordinator."""
        return getattr(self.coordinator, "smart_app", None)
    
    async def async_press(self) -> None:
        """Handle the button press."""
        if self._press_action:
            # Use custom press action if provided
            try:
                await self._press_action(self)
            except Exception as e:
                _LOGGER.error(f"Custom press action failed for {self._attr_name}: {e}")
        else:
            # Use standard command sending
            try:
                processed_value = self._command_processor(self._command_value)
                success = await self._send_command(self._command_type, processed_value)
                if success:
                    _LOGGER.info(
                        f"Button {self._attr_name} pressed successfully "
                        f"(entity_id: {self._attr_unique_id})"
                    )
            except Exception as e:
                _LOGGER.error(
                    f"Failed to press button {self._attr_name} "
                    f"(entity_id: {self._attr_unique_id}): {e}"
                )

# Button Action Functions
def create_toggle_action(power_command: str, on_value: Any = 1, off_value: Any = 0):
    """Create a toggle action for power buttons."""
    async def toggle_action(button_entity):
        try:
            # Get current power state using public method
            device_status = button_entity.get_device_status()
            current_power = device_status.get(power_command, 0)
            
            # Toggle the power state
            new_value = off_value if int(current_power) else on_value
            
            # Use public method to get smart_app
            smart_app = button_entity.get_smart_app()
            if smart_app:
                await smart_app.set_device_command(
                    button_entity._device_index, power_command, new_value
                )
                await button_entity.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error(
                f"Toggle action failed for {button_entity._attr_unique_id}: {e}"
            )
    
    return toggle_action

def create_sequence_action(commands: list):
    """Create a sequence action that sends multiple commands."""
    async def sequence_action(button_entity):
        smart_app = button_entity.get_smart_app()
        if not smart_app:
            return
            
        try:
            for command_type, value in commands:
                await smart_app.set_device_command(
                    button_entity._device_index, command_type, value
                )
            await button_entity.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error(
                f"Sequence action failed for {button_entity._attr_unique_id}: {e}"
            )
    
    return sequence_action

def create_conditional_action(condition_command: str, condition_value: Any, 
                            true_action: tuple, false_action: tuple):
    """Create a conditional action based on device state."""
    async def conditional_action(button_entity):
        try:
            device_status = button_entity.get_device_status()
            current_value = device_status.get(condition_command)
            
            if current_value == condition_value:
                command_type, value = true_action
            else:
                command_type, value = false_action
            
            smart_app = button_entity.get_smart_app()
            if smart_app:
                await smart_app.set_device_command(
                    button_entity._device_index, command_type, value
                )
                await button_entity.coordinator.async_request_refresh()
        except Exception as e:
            _LOGGER.error(
                f"Conditional action failed for {button_entity._attr_unique_id}: {e}"
            )
    
    return conditional_action

