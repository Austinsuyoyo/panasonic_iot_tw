"""命令處理工具類 - 統一處理設備命令邏輯"""
import logging
from typing import List, Dict, Tuple, Optional, Any

_LOGGER = logging.getLogger(__name__)


class CommandHelper:
    """統一的命令處理工具類，減少重複的命令查找和處理邏輯"""
    
    @staticmethod
    def get_command_parameters(commands: List[Dict], command_type: str) -> List[List]:
        """
        獲取指定命令類型的參數列表
        
        Args:
            commands: 命令列表
            command_type: 命令類型 (如 "0x01")
            
        Returns:
            參數列表，如果未找到返回空列表
        """
        try:
            for command in commands:
                if command.get("CommandType") == command_type:
                    return command.get("Parameters", [])
            
            _LOGGER.warning("Command type %s not found in commands", command_type)
            return []
            
        except (TypeError, KeyError) as e:
            _LOGGER.exception("Error getting command parameters for %s: %s", command_type, e)
            return []
    
    @staticmethod
    def find_parameter_by_value(parameters: List[List], value: int) -> Optional[Tuple[str, int]]:
        """
        根據數值查找參數
        
        Args:
            parameters: 參數列表 [[name, value], ...]
            value: 要查找的數值
            
        Returns:
            (name, value) 元組，如果未找到返回 None
        """
        try:
            for param in parameters:
                if len(param) >= 2 and param[1] == value:
                    return (param[0], param[1])
            
            _LOGGER.debug("Parameter with value %s not found", value)
            return None
            
        except (TypeError, IndexError) as e:
            _LOGGER.exception("Error finding parameter by value %s: %s", value, e)
            return None
    
    @staticmethod
    def find_parameter_by_name(parameters: List[List], name: str) -> Optional[Tuple[str, int]]:
        """
        根據名稱查找參數
        
        Args:
            parameters: 參數列表 [[name, value], ...]
            name: 要查找的名稱
            
        Returns:
            (name, value) 元組，如果未找到返回 None
        """
        try:
            for param in parameters:
                if len(param) >= 2 and param[0] == name:
                    return (param[0], param[1])
            
            _LOGGER.debug("Parameter with name '%s' not found", name)
            return None
            
        except (TypeError, IndexError) as e:
            _LOGGER.exception("Error finding parameter by name '%s': %s", name, e)
            return None
    
    @staticmethod
    def get_parameter_names(parameters: List[List]) -> List[str]:
        """
        獲取所有參數名稱
        
        Args:
            parameters: 參數列表
            
        Returns:
            參數名稱列表
        """
        try:
            return [param[0] for param in parameters if len(param) >= 1]
        except (TypeError, IndexError) as e:
            _LOGGER.exception("Error getting parameter names: %s", e)
            return []
    
    @staticmethod
    def get_current_option_name(
        commands: List[Dict], 
        command_type: str, 
        current_value: int
    ) -> Optional[str]:
        """
        獲取當前選項的名稱
        
        Args:
            commands: 命令列表
            command_type: 命令類型
            current_value: 當前數值
            
        Returns:
            選項名稱，如果未找到返回 None
        """
        parameters = CommandHelper.get_command_parameters(commands, command_type)
        if not parameters:
            return None
        
        result = CommandHelper.find_parameter_by_value(parameters, current_value)
        return result[0] if result else None
    
    @staticmethod
    def validate_option(
        commands: List[Dict], 
        command_type: str, 
        option_name: str
    ) -> bool:
        """
        驗證選項是否有效
        
        Args:
            commands: 命令列表
            command_type: 命令類型
            option_name: 選項名稱
            
        Returns:
            是否有效
        """
        parameters = CommandHelper.get_command_parameters(commands, command_type)
        if not parameters:
            return False
        
        return CommandHelper.find_parameter_by_name(parameters, option_name) is not None


class DeviceCommands:
    """設備命令常數定義"""
    
    class Power:
        """電源相關命令"""
        COMMAND = 128
        STATUS = "0x00"
        ON = 1
        OFF = 0
    
    class Temperature:
        """溫度相關命令"""
        SET_COMMAND = 3
        CURRENT_STATUS = "0x04"
        TARGET_STATUS = "0x03"
    
    class Mode:
        """模式相關命令"""
        SET_COMMAND = 129
        STATUS = "0x01"
    
    class Fan:
        """風扇相關命令"""
        SET_COMMAND = 130
        STATUS = "0x02"
    
    class Timer:
        """定時器相關命令"""
        ON_TIMER_COMMAND = 139
        OFF_TIMER_COMMAND = 140
        ON_TIMER_STATUS = "0x0B"
        OFF_TIMER_STATUS = "0x0C"