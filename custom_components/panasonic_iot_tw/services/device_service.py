"""Device data service - handles device information retrieval and command sending"""
import logging
from typing import Dict, List, Any

from .api_client import ApiClient
from .token_manager import TokenManager
from ..api_constants import API_ENDPOINTS
from ..base import ErrorHandler
from ..exceptions import (
    PanasonicLoginFailed,
    PanasonicTokenExpired,
    PanasonicRefreshTokenNotFound,
)

_LOGGER = logging.getLogger(__name__)


class DeviceService:
    """Device data service, responsible for device-related API operations"""
    
    def __init__(self, api_client: ApiClient, token_manager: TokenManager):
        """
        Initialize device service
        
        Args:
            api_client: API client instance
            token_manager: Token manager instance
        """
        self._api_client = api_client
        self._token_manager = token_manager
    
    async def get_device_list(self) -> List[Dict[str, Any]]:
        """
        Get device list
        
        Returns:
            Device list
        """
        _LOGGER.debug("Getting device list...")
        
        try:
            # Ensure authenticated
            await self._token_manager.ensure_authenticated()
            
            # Get authentication headers
            headers = self._token_manager.get_auth_headers()
            
            # Send request (use GET method, not POST)
            response = await self._api_client.request(
                method="GET",
                endpoint=API_ENDPOINTS["get_devices"],
                headers=headers
            )
            
            # Extract device list
            devices = response.get("GwList", [])
            
            # Update API client's device cache
            self._api_client.set_devices_cache(devices)

            _LOGGER.debug("Successfully retrieved %s devices", len(devices))
            return devices

        except (PanasonicLoginFailed, PanasonicTokenExpired, PanasonicRefreshTokenNotFound):
            # Authentication failures must propagate so the coordinator can
            # trigger re-authentication instead of masking them as UpdateFailed.
            raise
        except Exception as e:
            ErrorHandler.handle_coordinator_error(e, "get device list")
            return []
    
    async def get_device_status(
        self, 
        device: Dict[str, Any], 
        status_codes: List[str]
    ) -> Dict[str, Any]:
        """
        Get device status
        
        Args:
            device: Device information dictionary
            status_codes: Status code list
            
        Returns:
            Device status dictionary
        """
        device_id = device.get("Auth", "")
        device_name = device.get("NickName", "unknown device")

        try:
            # Ensure authenticated
            await self._token_manager.ensure_authenticated()
            
            # Get device authentication headers
            headers = self._token_manager.get_device_auth_headers(
                device_id=device_id,
                gwid=device.get("GWID")
            )
            
            # Prepare request data (according to original API format)
            commands = {"CommandTypes": [], "DeviceID": 1}
            for status_code in status_codes:
                commands["CommandTypes"].append({"CommandType": status_code})
            data = [commands]
            
            # Send request
            response = await self._api_client.request(
                method="POST",
                endpoint=API_ENDPOINTS["get_device_info"],
                headers=headers,
                data=data
            )
            
            # Process response (according to original API response format)
            status_dict = {}
            devices = response.get("devices", [])
            if devices:
                device = devices[0]
                for info in device.get("Info", []):
                    command_type = info.get("CommandType")
                    status = info.get("status")
                    if command_type and status is not None:
                        status_dict[command_type] = status

            return status_dict
            
        except Exception as e:
            # ErrorHandler logs all errors centrally
            ErrorHandler.handle_api_error(e, "get device status", device_name)
            return {}
    
    async def send_command(
        self, 
        device: Dict[str, Any], 
        command_type: str, 
        value: Any
    ) -> bool:
        """
        Send device command
        
        Args:
            device: Device information dictionary
            command_type: Command type
            value: Command value
            
        Returns:
            Whether sending was successful
        """
        device_id = device.get("Auth", "")
        device_name = device.get("NickName", "unknown device")
        
        _LOGGER.debug("Sending command to device %s: %s = %s", device_name, command_type, value)
        
        try:
            # Ensure authenticated
            await self._token_manager.ensure_authenticated()
            
            # Get device authentication headers
            headers = self._token_manager.get_device_auth_headers(
                device_id=device_id,
                gwid=device.get("GWID")
            )
            
            # Prepare command parameters (original API uses GET method and params)
            params = {
                "DeviceID": 1,
                "CommandType": command_type,
                "Value": value
            }
            
            # Send command (use GET method, not POST)
            await self._api_client.request(
                method="GET",
                endpoint=API_ENDPOINTS["set_command"],
                headers=headers,
                params=params
            )
            
            _LOGGER.debug("Device %s command sent successfully", device_name)
            return True
            
        except Exception as e:
            ErrorHandler.handle_api_error(e, "send device command", device_name)
            return False
    
    async def get_device_info(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get device detailed information

        Kept for future use; nothing calls it yet. Note that it posts to the
        UserGetInfo endpoint (account/report information), NOT DeviceGetInfo,
        which is the register-read endpoint used by get_device_status.

        Args:
            device: Device information dictionary

        Returns:
            Device detailed information
        """
        device_name = device.get("NickName", "unknown device")
        
        try:
            # Ensure authenticated
            await self._token_manager.ensure_authenticated()
            
            # Get device authentication headers
            headers = self._token_manager.get_device_auth_headers(
                device_id=device.get("Auth", ""),
                gwid=device.get("GWID")
            )
            
            # Send request
            response = await self._api_client.request(
                method="POST",
                endpoint=API_ENDPOINTS["get_info"],
                headers=headers,
                data={}
            )
            
            _LOGGER.debug("Device %s detailed information retrieved successfully", device_name)
            return response
            
        except Exception as e:
            ErrorHandler.handle_api_error(e, "get device detailed information", device_name)
            return {}