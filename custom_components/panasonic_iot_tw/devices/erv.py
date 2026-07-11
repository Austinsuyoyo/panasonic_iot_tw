"""ERV device logic for Panasonic IoT TW integration."""
import logging
from typing import Any, Dict, List, Optional

from ..base import BaseDevice

_LOGGER = logging.getLogger(__name__)


class ERVDevice(BaseDevice):
    """Energy Recovery Ventilator device logic."""
    
    # Command mappings
    POWER_COMMAND = "0x00"
    OPERATION_MODE_COMMAND = "0x15"
    FAN_LEVEL_COMMAND = "0x56"
    
    def __init__(self, coordinator, device_index: int, device_data: Dict[str, Any]):
        """Initialize ERV device."""
        super().__init__(coordinator, device_index, device_data)
    
    @property
    def is_on(self) -> bool:
        """Return if ERV is powered on."""
        return self.get_boolean_status(self.POWER_COMMAND)

    @property
    def operation_mode(self) -> Optional[int]:
        """Return current operation mode."""
        return self.get_int_status(self.OPERATION_MODE_COMMAND)

    @property
    def fan_level(self) -> Optional[int]:
        """Return current fan level."""
        return self.get_int_status(self.FAN_LEVEL_COMMAND)
    
    
    def get_select_entities(self, coordinator) -> List:
        """Return select entities for ERV."""
        operation_mode_options = {
            0: "停止",
            1: "自動",
            2: "低速",
            3: "中速",
            4: "高速",
            5: "換氣",
        }
        fan_level_options = {
            0: "停止",
            1: "低速",
            2: "中速",
            3: "高速",
        }
        
        return [
            # Operation mode select
            self._create_select(
                coordinator,
                command_type=self.OPERATION_MODE_COMMAND,
                name="運轉模式",
                select_key="operation_mode",
                options_dict=operation_mode_options,
                icon="mdi:fan-auto",
                translation_key="erv_operation_mode"
            ),
            # Fan level select
            self._create_select(
                coordinator,
                command_type=self.FAN_LEVEL_COMMAND,
                name="風量設定",
                select_key="fan_level",
                options_dict=fan_level_options,
                icon="mdi:fan",
                translation_key="erv_fan_level"
            )
        ]