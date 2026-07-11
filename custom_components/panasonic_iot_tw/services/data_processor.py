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
    
    def merge_device_data(
        self, 
        devices: List[Dict[str, Any]], 
        statuses: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Merge device list and status data
        
        Args:
            devices: Device list
            statuses: Device status dictionary {device_id: status_data}
            
        Returns:
            Merged device data dictionary {device_id: merged_data}
        """
        merged_data = {}
        
        for device in devices:
            device_id = device.get("device_id")
            if not device_id:
                continue
            
            # Merge device information and status
            merged_device = device.copy()
            
            # Add status information
            if device_id in statuses:
                status_data = statuses[device_id]
                merged_device.update({
                    "status": status_data.get("status", {}),
                    "available": status_data.get("available", False),
                    "last_update": status_data.get("timestamp"),
                })
            else:
                merged_device.update({
                    "status": {},
                    "available": False,
                    "last_update": None,
                })
            
            merged_data[device_id] = merged_device
        
        return merged_data
    
    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device information by device ID
        
        Args:
            device_id: Device ID
            
        Returns:
            Device information
        """
        return self._device_cache.get(device_id)
    
    def get_device_type_name(self, device_type: int) -> str:
        """
        Get device type name by device type code
        
        Args:
            device_type: Device type code
            
        Returns:
            Device type name
        """
        type_mapping = {
            1: "Air Conditioner",
            2: "Refrigerator", 
            3: "Washing Machine",
            4: "Dehumidifier",
            6: "Dryer",
            8: "Air Purifier",
            14: "ERV",
            17: "Smart Switch",
        }
        
        return type_mapping.get(device_type, f"Unknown device type ({device_type})")
    
    def validate_device_data(self, device_data: Dict[str, Any]) -> bool:
        """
        Validate device data integrity
        
        Args:
            device_data: Device data
            
        Returns:
            Whether valid
        """
        required_fields = ["device_id", "nickname", "device_type"]
        
        for field in required_fields:
            if field not in device_data:
                _LOGGER.warning("Device data missing required field: %s", field)
                return False
        
        return True
    
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