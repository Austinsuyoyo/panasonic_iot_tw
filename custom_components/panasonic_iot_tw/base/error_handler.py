"""Error handling utility class - unified handling of various exception scenarios"""
import logging
from typing import Any, Dict, Optional
from homeassistant.helpers.update_coordinator import UpdateFailed
from ..exceptions import (
    PanasonicDeviceOffline,
    PanasonicExceedRateLimit,
    PanasonicTokenExpired,
    PanasonicLoginFailed,
    PanasonicBaseException
)

_LOGGER = logging.getLogger(__name__)


class ErrorHandler:
    """Unified error handling class"""
    
    @staticmethod
    def handle_api_error(e: Exception, context: str, device_name: str = None, log_offline: bool = True) -> Dict[str, Any]:
        """
        Handle API errors

        Args:
            e: Exception object
            context: Error context
            device_name: Device name (optional)
            log_offline: Whether to log offline status (default True, set False to suppress duplicate logs)

        Returns:
            Error handling result dictionary
        """
        device_info = f" for device '{device_name}'" if device_name else ""

        if isinstance(e, PanasonicDeviceOffline):
            if log_offline:
                _LOGGER.debug(f"Device{device_info} is offline in {context}: {e}")
            return {"status": "offline", "data": {}, "message": str(e)}
        
        elif isinstance(e, PanasonicExceedRateLimit):
            _LOGGER.error(f"Rate limit exceeded in {context}{device_info}")
            return {"status": "rate_limited", "data": {}, "should_retry": True}
        
        elif isinstance(e, PanasonicTokenExpired):
            _LOGGER.warning(f"Token expired in {context}{device_info}")
            return {"status": "token_expired", "data": {}, "should_retry": True}
        
        elif isinstance(e, PanasonicLoginFailed):
            _LOGGER.warning(f"Login failed in {context}{device_info}: {e}")
            return {"status": "login_failed", "data": {}, "should_retry": False}
        
        elif isinstance(e, PanasonicBaseException):
            _LOGGER.error(f"Panasonic API error in {context}{device_info}: {e}")
            return {"status": "api_error", "data": {}, "should_retry": True}
        
        else:
            _LOGGER.exception(f"Unexpected error in {context}{device_info}")
            return {"status": "unknown_error", "data": {}, "should_retry": False}
    
    @staticmethod
    def handle_coordinator_error(e: Exception, context: str) -> None:
        """
        Handle coordinator errors, raise appropriate UpdateFailed
        
        Args:
            e: Exception object
            context: Error context
        """
        error_result = ErrorHandler.handle_api_error(e, context)
        
        if error_result["status"] in ["rate_limited", "token_expired"]:
            # These errors can be retried
            raise UpdateFailed(f"Temporary failure in {context}: {str(e)}")
        elif error_result["status"] == "offline":
            return
        else:
            # Other errors
            raise UpdateFailed(f"Failed in {context}: {str(e)}")
    
    @staticmethod
    def safe_execute(func, default_value=None, context: str = "unknown") -> Any:
        """
        Safely execute function, catch exceptions and return default value
        
        Args:
            func: Function to execute
            default_value: Default return value
            context: Execution context
            
        Returns:
            Function execution result or default value
        """
        try:
            return func()
        except Exception as e:
            _LOGGER.warning(f"Safe execution failed in {context}: {e}")
            return default_value
    
    @staticmethod
    def validate_response(response: Dict, required_keys: list, context: str = "API response") -> bool:
        """
        Validate API response format
        
        Args:
            response: API response dictionary
            required_keys: Required key list
            context: Validation context
            
        Returns:
            Whether validation passed
        """
        if not isinstance(response, dict):
            _LOGGER.error(f"Invalid response format in {context}: not a dictionary")
            return False
        
        missing_keys = [key for key in required_keys if key not in response]
        if missing_keys:
            _LOGGER.error(f"Missing required keys in {context}: {missing_keys}")
            return False
        
        return True
    
    @staticmethod
    def log_device_status(device_name: str, status: str, details: Optional[str] = None):
        """
        Log device status
        
        Args:
            device_name: Device name
            status: Status
            details: Detailed information
        """
        message = f"Device '{device_name}' status: {status}"
        if details:
            message += f" - {details}"
        
        if status in ["offline", "error", "failed"]:
            _LOGGER.warning(message)
        elif status in ["online", "success", "updated", "login_success", "token_refreshed", "logout"]:
            _LOGGER.debug(message)
        else:
            _LOGGER.info(message)