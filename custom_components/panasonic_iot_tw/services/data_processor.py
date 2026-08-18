"""Data processor - handles conversion and processing of API response data"""
import logging
from typing import Dict, List, Any, Optional

_LOGGER = logging.getLogger(__name__)


class DataProcessor:
    """Data processor, responsible for API data conversion and standardization"""
    
    def __init__(self):
        """Initialize data processor"""
        self._device_cache = {}
    
    def process_device_list(self, raw_devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process device list data
        
        Args:
            raw_devices: Raw device list
            
        Returns:
            Processed device list
        """
        processed_devices = []
        
        for device in raw_devices:
            try:
                processed_device = self._process_single_device(device)
                if processed_device:
                    processed_devices.append(processed_device)
                    # Update device cache
                    device_id = processed_device.get("device_id")
                    if device_id:
                        self._device_cache[device_id] = processed_device
            except Exception as e:
                _LOGGER.warning("Error occurred while processing device data: %s", e)
                continue
        
        _LOGGER.debug("Processing completed, total %s valid devices", len(processed_devices))
        return processed_devices
    
    def _process_single_device(self, device: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process single device data
        
        Args:
            device: Raw device data
            
        Returns:
            Processed device data
        """
        # Extract basic information
        device_id = device.get("Auth")
        if not device_id:
            _LOGGER.warning("Device missing Auth field, skipping")
            return None
        
        # Convert device type to integer for proper lookup
        device_type_raw = device.get("DeviceType", 0)
        try:
            device_type = int(device_type_raw) if device_type_raw else 0
        except (ValueError, TypeError):
            _LOGGER.warning("Unable to convert device type '%s' to integer, using default value 0", device_type_raw)
            device_type = 0
        
        processed = {
            "device_id": device_id,
            "auth": device_id,
            "gwid": device.get("GWID"),
            "nickname": device.get("NickName", "unknown device"),
            "model": device.get("Model", "unknown model"),
            "device_type": device_type,
            "online": device.get("Online", False),
            "raw_data": device,  # Keep raw data for future use
        }
        
        return processed
    
    def process_device_status(
        self, 
        device_id: str, 
        raw_status: Dict[str, Any],
        status_codes: List[str]
    ) -> Dict[str, Any]:
        """
        Process device status data
        
        Args:
            device_id: Device ID
            raw_status: Raw status data
            status_codes: Requested status code list
            
        Returns:
            Processed status data
        """
        processed_status = {
            "device_id": device_id,
            "status": {},
            "timestamp": None,
            "available": True,
        }
        
        try:
            # Process status data
            for status_code in status_codes:
                if status_code in raw_status:
                    processed_status["status"][status_code] = raw_status[status_code]
            
            # Check if device is available
            if not processed_status["status"]:
                processed_status["available"] = False
            
        except Exception as e:
            _LOGGER.error("Error occurred while processing device %s status: %s", device_id, e)
            processed_status["available"] = False
        
        return processed_status
    
    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device information by device ID
        
        Args:
            device_id: Device ID
            
        Returns:
            Device information
        """
        return self._device_cache.get(device_id)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics
        """
        return {
            "cached_devices": len(self._device_cache),
            "device_ids": list(self._device_cache.keys()),
        }