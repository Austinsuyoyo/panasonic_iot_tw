"""SmartApp main service coordinator - unified interface and service orchestration"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple

from .api_client import ApiClient
from .token_manager import TokenManager
from .device_service import DeviceService
from .data_processor import DataProcessor
from .report_service import ReportService
from ..exceptions import (
    PanasonicExceedRateLimit,
    PanasonicDeviceOffline,
    PanasonicLoginFailed,
    PanasonicTokenExpired,
)
from ..base import ErrorHandler

_LOGGER = logging.getLogger(__name__)


class SmartApp:
    """
    SmartApp main service coordinator
    
    Responsibilities:
    - Service coordination and unified interface
    - Unified error handling and retry mechanisms
    - Data caching and state management
    """
    
    def __init__(self, session, account: str, password: str, proxy: Optional[str] = None):
        """
        Initialize SmartApp
        
        Args:
            session: aiohttp session
            account: User account
            password: User password
            proxy: Proxy server configuration
        """
        self.account = account
        self.password = password
        
        # Initialize service layer
        self._api_client = ApiClient(session, proxy)
        self._token_manager = TokenManager(self._api_client, account, password)
        self._device_service = DeviceService(self._api_client, self._token_manager)
        self._data_processor = DataProcessor()
        self._report_service = ReportService(self._api_client, self._token_manager)
        
        # Statistics information
        self._operation_count = 0
        self._last_successful_update = None
        
        # Device cache
        self._devices_cache = {}
        self._device_list_cache = []
        
        # Special sensor data cache - managed by report service
        self._special_data_cache = {
            "energy": {},
            "co2": {},
            "door": {}
        }
        
    def set_initialization_mode(self, enabled: bool) -> None:
        """
        Set initialization mode for faster device setup
        
        Args:
            enabled: Whether to enable initialization mode
        """
        self._api_client.set_initialization_mode(enabled)
        _LOGGER.debug(f"Initialization mode {'enabled' if enabled else 'disabled'}")
    
    async def _fetch_special_data_for_devices(self, devices: List[Dict[str, Any]]) -> None:
        """
        Fetch special sensor data (energy, CO2, door) for supported devices
        
        Args:
            devices: List of device information
        """
        try:
            # Filter devices that support special sensors
            supported_devices = [
                device for device in devices 
                if device.get("device_type") in self._report_service.SUPPORTED_DEVICE_TYPES
            ]
            
            if not supported_devices:
                _LOGGER.debug("No devices support special sensors")
                return
            
            # Fetch all three types of special data concurrently
            try:
                await asyncio.gather(
                    self._report_service.get_energy_data(supported_devices),
                    self._report_service.get_co2_data(supported_devices),
                    self._report_service.get_door_data(supported_devices),
                    return_exceptions=True
                )
                # Log cache status summary
                cache_age = self._report_service.get_cache_age_hours()
                if cache_age:
                    _LOGGER.debug(f"Special sensor data ready (cached: {cache_age:.1f}h old)")
            except Exception as e:
                _LOGGER.warning(f"Failed to fetch some special sensor data: {e}")
                
        except Exception as e:
            _LOGGER.error(f"Error in special data fetch: {e}")
    
    async def force_refresh_special_data(self) -> bool:
        """
        Force refresh all special sensor data (energy, CO2, door) regardless of cache status.
        
        This method bypasses the daily update logic and forces immediate data fetch.
        Useful for manual refresh or debugging.
        
        Returns:
            True if refresh was successful
        """
        try:
            _LOGGER.info("Force refreshing special sensor data...")
            
            # Get current device list
            devices = await self.get_devices()
            if not devices:
                _LOGGER.warning("No devices found for special data refresh")
                return False
            
            # Filter devices that support special sensors
            supported_devices = [
                device for device in devices 
                if device.get("device_type") in self._report_service.SUPPORTED_DEVICE_TYPES
            ]
            
            if not supported_devices:
                _LOGGER.info("No devices support special sensors")
                return True
            
            # Clear cache timestamps to force refresh
            self._report_service._last_energy_fetch = None
            self._report_service._last_co2_fetch = None
            self._report_service._last_door_fetch = None
            
            _LOGGER.info(f"Force fetching special data for {len(supported_devices)} devices")
            
            # Fetch all special data
            results = await asyncio.gather(
                self._report_service.get_energy_data(supported_devices),
                self._report_service.get_co2_data(supported_devices),
                self._report_service.get_door_data(supported_devices),
                return_exceptions=True
            )
            
            # Check if any requests succeeded
            success_count = sum(1 for result in results if not isinstance(result, Exception))
            total_count = len(results)
            
            _LOGGER.info(f"Special data force refresh completed: {success_count}/{total_count} successful")
            return success_count > 0
            
        except Exception as e:
            _LOGGER.error(f"Error in force refresh special data: {e}")
            return False
    
    async def login(self) -> Dict[str, str]:
        """
        User login
        
        Returns:
            Login result
        """
        _LOGGER.info("SmartApp starting login...")
        self._operation_count += 1

        try:
            result = await self._token_manager.login()
            _LOGGER.info("SmartApp login successful")
            return result
        except (PanasonicLoginFailed, PanasonicExceedRateLimit, PanasonicTokenExpired) as e:
            # These are expected exceptions, re-raise without additional logging
            # The specific error is already logged at lower level
            raise
        except Exception as e:
            _LOGGER.error(f"Unexpected error during login: {e}")
            raise
    
    async def get_devices(self) -> List[Dict[str, Any]]:
        """
        Get device list

        Returns:
            Processed device list
        """
        self._operation_count += 1

        try:
            # Get raw device list (device_service will log this)
            raw_devices = await self._device_service.get_device_list()
            
            # Process device data
            processed_devices = self._data_processor.process_device_list(raw_devices)
            
            # Update cache
            self._device_list_cache = processed_devices
            
            return processed_devices
            
        except Exception as e:
            _LOGGER.error(f"Failed to get device list: {e}")
            # Return cached device list (if available)
            return self._device_list_cache
    
    async def get_device_with_info(self, status_codes_dict: Dict[int, List[Union[str, Tuple[str, bool]]]]) -> Dict[str, Dict[str, Any]]:
        """
        Get devices and their status information
        
        Args:
            status_codes_dict: Mapping from device type to status codes
            
        Returns:
            Device information dictionary {device_index: device_data}
        """
        _LOGGER.debug("Getting device detailed information...")
        self._operation_count += 1
        
        try:
            # Get device list
            devices = await self.get_devices()
            
            if not devices:
                _LOGGER.warning("No devices found")
                return {}
            
            # Get status of all devices
            device_data = {}
            for index, device in enumerate(devices):
                device_type = device.get("device_type", 0)
                status_codes_raw = status_codes_dict.get(device_type, [])
                
                # Extract enabled status codes from tuples
                if status_codes_raw and isinstance(status_codes_raw[0], tuple):
                    # New tuple format: (code, enabled)
                    status_codes = [code for code, enabled in status_codes_raw if enabled]
                else:
                    # Legacy string format
                    status_codes = status_codes_raw
                
                if not status_codes:
                    _LOGGER.warning(f"Device type {device_type} has no enabled status codes, using basic status codes")
                    # Use basic status codes to try to get device information
                    status_codes = ["0x00", "0x50", "0x55"]
                
                # Get device status
                status = await self._device_service.get_device_status(
                    device.get("raw_data", {}), 
                    status_codes
                )
                
                # Process status data
                processed_status = self._data_processor.process_device_status(
                    device.get("device_id", ""), 
                    status, 
                    status_codes
                )
                
                # Merge device information and status
                device_data[index] = {
                    **device,
                    "status": processed_status.get("status", {}),
                    "available": processed_status.get("available", False),
                }
            
            # Update cache
            self._devices_cache = device_data
            self._last_successful_update = asyncio.get_event_loop().time()
            
            # Fetch special sensor data for supported devices (async, non-blocking)
            await self._fetch_special_data_for_devices(devices)

            # Log summary of successful update
            available_count = sum(1 for d in device_data.values() if d.get("available", False))
            _LOGGER.debug(f"Updated {len(device_data)} devices ({available_count} available)")
            return device_data
            
        except Exception as e:
            _LOGGER.error(f"Failed to get device detailed information: {e}")
            # Return cached device data (if available)
            return self._devices_cache
    
    async def set_device_command(
        self, 
        device_index: int, 
        command_type: str, 
        value: Any
    ) -> bool:
        """
        Set device command
        
        Args:
            device_index: Device index
            command_type: Command type
            value: Command value
            
        Returns:
            Whether successful
        """
        _LOGGER.info(f"Setting device {device_index} command: {command_type} = {value}")
        self._operation_count += 1
        
        try:
            # Get device information
            if device_index not in self._devices_cache:
                _LOGGER.error(f"Device index {device_index} does not exist")
                return False
            
            device = self._devices_cache[device_index]
            raw_device = device.get("raw_data", {})
            
            # Send command
            success = await self._device_service.send_command(
                raw_device, 
                command_type, 
                value
            )
            
            if success:
                _LOGGER.info(f"Device {device_index} command set successfully")
            else:
                _LOGGER.warning(f"Device {device_index} command set failed")
            
            return success
            
        except Exception as e:
            _LOGGER.error(f"Failed to set device command: {e}")
            return False
    
    async def get_special_sensor_data(self, device_list: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get special sensor data (energy, CO2, door) for supported devices.
        
        Args:
            device_list: Optional device list, if None will use cached device list
            
        Returns:
            Dictionary with energy, CO2, and door data for supported devices
        """
        _LOGGER.info("Getting special sensor data...")
        self._operation_count += 1
        
        try:
            # Use provided device list or cached device list
            devices = device_list if device_list is not None else self._device_list_cache
            
            if not devices:
                _LOGGER.warning("No devices available for special sensor data")
                return {"energy": {}, "co2": {}, "door": {}}
            
            # Get all special data from report service
            special_data = await self._report_service.get_all_special_data(devices)
            
            # Update cache
            self._special_data_cache.update(special_data)
            
            _LOGGER.info(f"Retrieved special sensor data: "
                        f"energy={len(special_data.get('energy', {}))}, "
                        f"co2={len(special_data.get('co2', {}))}, "
                        f"door={len(special_data.get('door', {}))}")
            
            return special_data
            
        except Exception as e:
            _LOGGER.error(f"Failed to get special sensor data: {e}")
            # Return cached data
            return self._special_data_cache
    
    def get_device_energy_data(self, device_gwid: str) -> Optional[Dict[str, Any]]:
        """
        Get energy consumption data for a specific device.
        
        Args:
            device_gwid: Device GWID
            
        Returns:
            Energy data for the device or None
        """
        return self._report_service.get_cached_energy_data(device_gwid)
    
    def get_device_co2_data(self, device_gwid: str) -> Optional[Dict[str, Any]]:
        """
        Get CO2 footprint data for a specific device.
        
        Args:
            device_gwid: Device GWID
            
        Returns:
            CO2 data for the device or None
        """
        return self._report_service.get_cached_co2_data(device_gwid)
    
    def get_device_door_data(self, device_gwid: str) -> Optional[Dict[str, Any]]:
        """
        Get door open count data for a specific device.
        
        Args:
            device_gwid: Device GWID
            
        Returns:
            Door data for the device or None
        """
        return self._report_service.get_cached_door_data(device_gwid)
    
    def get_device_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get device information by index
        
        Args:
            index: Device index
            
        Returns:
            Device information
        """
        return self._devices_cache.get(index)
    
    def get_all_devices(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all device information
        
        Returns:
            All device information
        """
        return self._devices_cache.copy()
    
    def logout(self) -> None:
        """Logout and clear all cache"""
        _LOGGER.debug("SmartApp logout")
        
        self._token_manager.logout()
        self._devices_cache.clear()
        self._device_list_cache.clear()
        self._special_data_cache = {"energy": {}, "co2": {}, "door": {}}
        self._report_service.clear_cache()
        self._last_successful_update = None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics information
        
        Returns:
            Statistics information
        """
        return {
            "account": self.account,
            "operation_count": self._operation_count,
            "last_successful_update": self._last_successful_update,
            "cached_devices": len(self._devices_cache),
            "token_info": self._token_manager.get_token_info(),
            "api_stats": self._api_client.get_request_stats(),
            "cache_stats": self._data_processor.get_cache_stats(),
            "report_cache_stats": self._report_service.get_cache_stats(),
        }
    
    
    
    def __repr__(self) -> str:
        """String representation"""
        device_count = len(self._devices_cache)
        auth_status = "authenticated" if self._token_manager.is_authenticated else "unauthenticated"
        return f"SmartApp(account={self.account}, devices={device_count}, auth={auth_status})"