"""Command processing utilities - unifies device command handling logic."""
import logging
from typing import List, Dict, Tuple, Optional, Any

_LOGGER = logging.getLogger(__name__)


class CommandHelper:
    """Unified command processing helper, reduces duplicate command lookup/handling logic."""
    
    @staticmethod
    def get_command_parameters(commands: List[Dict], command_type: str) -> List[List]:
        """
        Get the parameter list for a given command type.
        
        Args:
            commands: Command list
            command_type: Command type (e.g. "0x01")
            
        Returns:
            Parameter list, or an empty list if not found
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
        Find a parameter by value.
        
        Args:
            parameters: Parameter list [[name, value], ...]
            value: The value to look up
            
        Returns:
            (name, value) tuple, or None if not found
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
        Find a parameter by name.
        
        Args:
            parameters: Parameter list [[name, value], ...]
            name: The name to look up
            
        Returns:
            (name, value) tuple, or None if not found
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
        Get all parameter names.
        
        Args:
            parameters: Parameter list
            
        Returns:
            List of parameter names
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
        Get the name of the current option.
        
        Args:
            commands: Command list
            command_type: Command type
            current_value: Current value
            
        Returns:
            Option name, or None if not found
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
        Validate whether an option is valid.
        
        Args:
            commands: Command list
            command_type: Command type
            option_name: Option name
            
        Returns:
            Whether the option is valid
        """
        parameters = CommandHelper.get_command_parameters(commands, command_type)
        if not parameters:
            return False
        
        return CommandHelper.find_parameter_by_name(parameters, option_name) is not None


class DeviceCommands:
    """Device command constant definitions"""
    
    class Power:
        """Power-related commands"""
        COMMAND = 128
        STATUS = "0x00"
        ON = 1
        OFF = 0
    
    class Temperature:
        """Temperature-related commands"""
        SET_COMMAND = 3
        CURRENT_STATUS = "0x04"
        TARGET_STATUS = "0x03"
    
    class Mode:
        """Mode-related commands"""
        SET_COMMAND = 129
        STATUS = "0x01"
    
    class Fan:
        """Fan-related commands"""
        SET_COMMAND = 130
        STATUS = "0x02"
    
    class Timer:
        """Timer-related commands"""
        ON_TIMER_COMMAND = 139
        OFF_TIMER_COMMAND = 140
        ON_TIMER_STATUS = "0x0B"
        OFF_TIMER_STATUS = "0x0C"