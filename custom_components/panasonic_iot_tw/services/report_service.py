"""Smart report service for energy/CO2/door data with device filtering and caching."""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta

from .api_client import ApiClient
from .token_manager import TokenManager
from ..api_constants import API_ENDPOINTS
from ..const import DEVICE_TYPE_REFRIGERATOR

_LOGGER = logging.getLogger(__name__)

# The report API (UserGetInfo) is unreliable between local midnight and this
# hour: the backend rolls its day over on an 8h-ahead schedule, so requests in
# this window reliably error or return empty results. Defer the daily refresh
# until the window closes instead of hammering a broken endpoint all night.
NIGHTLY_MAINTENANCE_END_HOUR = 8

# After a failed report fetch, wait this long before retrying instead of
# retrying on every coordinator cycle (~180s) and spamming errors.
FAILURE_RETRY_SECONDS = 1800


class ReportService:
    """
    Smart report service that handles energy, CO2, and door open data.
    
    Features:
    - Global API calls to reduce request volume (3 calls instead of 9)
    - Device filtering to only request data for supported devices
    - Smart caching to avoid frequent API requests
    - English comments throughout
    """
    
    # Device type support mapping - only refrigerators support these features
    SUPPORTED_DEVICE_TYPES = {DEVICE_TYPE_REFRIGERATOR}
    
    # Cache duration in seconds (24 hours)
    CACHE_DURATION = 86400
    
    def __init__(self, api_client: ApiClient, token_manager: TokenManager):
        """Initialize report service with API client and token manager."""
        self.api_client = api_client
        self.token_manager = token_manager
        
        # Cache for report data
        self._energy_cache = {}
        self._co2_cache = {}
        self._door_cache = {}
        
        # Cache timestamps
        self._last_energy_fetch = None
        self._last_co2_fetch = None
        self._last_door_fetch = None
        
        # Track which devices support which features
        self._supported_devices_cache = set()

        # Timestamp of the most recent failed fetch, shared across all three
        # report types, used to back off instead of retrying every cycle.
        self._last_failed_fetch: Optional[datetime] = None

    def get_cache_age_hours(self) -> Optional[float]:
        """Get the age of cached data in hours (using most recent cache timestamp)."""
        timestamps = [t for t in [self._last_energy_fetch, self._last_co2_fetch, self._last_door_fetch] if t]
        if not timestamps:
            return None
        most_recent = max(timestamps)
        return (datetime.now() - most_recent).total_seconds() / 3600

    def _is_daily_update_needed(self, last_fetch_time: Optional[datetime]) -> bool:
        """
        Check if daily update is needed based on smart scheduling.

        Updates are needed when:
        1. Never fetched before (startup best effort, even during the night)
        2. Last fetch was on a different day AND the nightly maintenance window
           has closed (local hour >= NIGHTLY_MAINTENANCE_END_HOUR)
        3. Cache has expired (24+ hours)

        The date-change refresh is deliberately held back until the maintenance
        window closes: the report backend rolls its day over ~8h ahead of
        Taipei time, so the first post-midnight poll would otherwise hit a
        broken endpoint. The daily refresh therefore lands on the first poll
        at/after NIGHTLY_MAINTENANCE_END_HOUR rather than at midnight.

        Args:
            last_fetch_time: Timestamp of last successful fetch

        Returns:
            True if update is needed
        """
        if last_fetch_time is None:
            _LOGGER.debug("Special data update needed: never fetched before")
            return True

        now = datetime.now()

        # Check if it's a different day (simple daily check)
        if last_fetch_time.date() != now.date():
            if now.hour >= NIGHTLY_MAINTENANCE_END_HOUR:
                _LOGGER.debug("Special data daily update needed: last fetch was %s, now %s", last_fetch_time.date(), now.date())
                return True
            _LOGGER.debug("Special data date changed but waiting out nightly maintenance window, serving cached data")
            return False

        # Check if cache has expired (fallback safety)
        time_since_last = (now - last_fetch_time).total_seconds()
        if time_since_last > self.CACHE_DURATION:
            _LOGGER.warning("Special data cache expired: %s hours since last fetch", time_since_last / 3600)
            return True

        # Cache is fresh, no need to log (individual cache usage will be logged once)
        return False

    def _should_fetch_data(self, last_fetch_time: Optional[datetime]) -> bool:
        """
        Check if data should be fetched based on daily update and backoff logic.

        A recent failure suppresses fetches for FAILURE_RETRY_SECONDS so a
        broken API is retried every ~30 min instead of every coordinator
        cycle; this applies to the never-fetched startup path as well. A
        missing timestamp (never fetched, or reset by
        force_refresh_special_data, which also clears the failure backoff)
        bypasses the maintenance-hour gate.
        """
        if self._last_failed_fetch is not None:
            elapsed = (datetime.now() - self._last_failed_fetch).total_seconds()
            if elapsed < FAILURE_RETRY_SECONDS:
                _LOGGER.debug("Special data fetch backing off: %.0fs since last failure", elapsed)
                return False

        if last_fetch_time is None:
            return True

        return self._is_daily_update_needed(last_fetch_time)
    
    def _get_current_month_date(self) -> str:
        """Get current month start date in YYYY/MM/DD format."""
        now = datetime.now()
        return f"{now.year}/{now.month:02d}/01"
    
    async def _make_report_request(self, report_type: str, report_name: str) -> Optional[Dict[str, Any]]:
        """
        Make a report request to the UserGetInfo endpoint.
        
        Args:
            report_type: Type identifier for the request
            report_name: Human readable name for logging
            
        Returns:
            API response data or None if failed
        """
        try:
            headers = {
                "cptoken": self.token_manager.cp_token,
                "Content-Type": "application/json",
                "User-Agent": "okhttp/4.9.1"
            }
            
            payload = {
                "name": report_type,
                "from": self._get_current_month_date(),
                "unit": "day",
                "max_num": 31
            }
            
            info_url = API_ENDPOINTS.get("get_info", f"{API_ENDPOINTS['login'].replace('/userlogin1', '')}/UserGetInfo")
            
            _LOGGER.debug("Requesting %s data from %s", report_name, info_url)
            
            response = await self.api_client.post(info_url, headers=headers, json=payload)
            
            if response and isinstance(response, dict):
                _LOGGER.debug("Successfully fetched %s data", report_name)
                return response
            else:
                _LOGGER.warning("Invalid response format for %s: %s", report_name, type(response))
                return None
                
        except Exception as e:
            _LOGGER.error("Failed to fetch %s data: %s", report_name, e)
            return None
    
    def _has_supported_devices(self, device_list: List[Dict[str, Any]]) -> bool:
        """Check if any devices in the list support special sensor features."""
        return any(
            device.get("device_type") in self.SUPPORTED_DEVICE_TYPES 
            for device in device_list
        )
    
    def _extract_device_data(self, report_data: Dict[str, Any], device_gwid: str) -> Optional[Dict[str, Any]]:
        """
        Extract data for a specific device from report response.
        
        Args:
            report_data: Full report response
            device_gwid: Device GWID to find
            
        Returns:
            Device-specific data or None if not found
        """
        if not report_data or not isinstance(report_data, dict):
            return None
        
        # Look for device in GwList
        gw_list = report_data.get("GwList", [])
        for device_data in gw_list:
            if device_data.get("GwID") == device_gwid:
                return device_data
        
        return None
    
    async def get_energy_data(self, device_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Get energy consumption data for supported devices.
        
        Args:
            device_list: List of all devices
            
        Returns:
            Dictionary mapping device GWID to energy data
        """
        # Check if we have supported devices
        if not self._has_supported_devices(device_list):
            _LOGGER.debug("No devices support energy data, skipping request")
            return {}
        
        # Check cache
        if not self._should_fetch_data(self._last_energy_fetch):
            return self._energy_cache
        
        # Fetch fresh data
        report_data = await self._make_report_request("Power", "Energy")

        # Extract data for each supported device
        energy_data = {}
        if report_data:
            for device in device_list:
                if device.get("device_type") in self.SUPPORTED_DEVICE_TYPES:
                    device_gwid = device.get("gwid")
                    if device_gwid:
                        device_energy = self._extract_device_data(report_data, device_gwid)
                        if device_energy:
                            energy_data[device_gwid] = device_energy

        # Treat a missing response, or an empty result while we still hold a
        # good cache, as a failure (nightly maintenance / transient outage):
        # keep the existing cache, don't advance the timestamp, and back off.
        if report_data is None or (not energy_data and self._energy_cache):
            _LOGGER.warning("Energy fetch failed or returned empty, keeping cached data")
            self._last_failed_fetch = datetime.now()
            return self._energy_cache

        # Update cache
        self._energy_cache = energy_data
        self._last_energy_fetch = datetime.now()
        self._last_failed_fetch = None

        _LOGGER.debug("Cached energy data for %s devices", len(energy_data))
        return energy_data
    
    async def get_co2_data(self, device_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Get CO2 footprint data for supported devices.
        
        Args:
            device_list: List of all devices
            
        Returns:
            Dictionary mapping device GWID to CO2 data
        """
        # Check if we have supported devices
        if not self._has_supported_devices(device_list):
            _LOGGER.debug("No devices support CO2 data, skipping request")
            return {}
        
        # Check cache
        if not self._should_fetch_data(self._last_co2_fetch):
            return self._co2_cache
        
        # Fetch fresh data
        report_data = await self._make_report_request("CO2", "CO2 Footprint")

        # Extract data for each supported device
        co2_data = {}
        if report_data:
            for device in device_list:
                if device.get("device_type") in self.SUPPORTED_DEVICE_TYPES:
                    device_gwid = device.get("gwid")
                    if device_gwid:
                        device_co2 = self._extract_device_data(report_data, device_gwid)
                        if device_co2:
                            co2_data[device_gwid] = device_co2

        # See get_energy_data: empty result with a live cache means the report
        # backend is in its nightly window / transient failure. Preserve cache.
        if report_data is None or (not co2_data and self._co2_cache):
            _LOGGER.warning("CO2 fetch failed or returned empty, keeping cached data")
            self._last_failed_fetch = datetime.now()
            return self._co2_cache

        # Update cache
        self._co2_cache = co2_data
        self._last_co2_fetch = datetime.now()
        self._last_failed_fetch = None

        _LOGGER.debug("Cached CO2 data for %s devices", len(co2_data))
        return co2_data
    
    async def get_door_data(self, device_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Get door open count data for supported devices.
        
        Args:
            device_list: List of all devices
            
        Returns:
            Dictionary mapping device GWID to door data
        """
        # Check if we have supported devices
        if not self._has_supported_devices(device_list):
            _LOGGER.debug("No devices support door data, skipping request")
            return {}
        
        # Check cache
        if not self._should_fetch_data(self._last_door_fetch):
            return self._door_cache
        
        # Fetch fresh data
        report_data = await self._make_report_request("Other", "Door Open Count")

        # Extract data for each supported device
        door_data = {}
        if report_data:
            for device in device_list:
                if device.get("device_type") in self.SUPPORTED_DEVICE_TYPES:
                    device_gwid = device.get("gwid")
                    if device_gwid:
                        device_door = self._extract_device_data(report_data, device_gwid)
                        if device_door:
                            door_data[device_gwid] = device_door

        # See get_energy_data: empty result with a live cache means the report
        # backend is in its nightly window / transient failure. Preserve cache.
        if report_data is None or (not door_data and self._door_cache):
            _LOGGER.warning("Door fetch failed or returned empty, keeping cached data")
            self._last_failed_fetch = datetime.now()
            return self._door_cache

        # Update cache
        self._door_cache = door_data
        self._last_door_fetch = datetime.now()
        self._last_failed_fetch = None

        _LOGGER.debug("Cached door data for %s devices", len(door_data))
        return door_data
    
    async def get_all_special_data(self, device_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Get all special sensor data (energy, CO2, door) in parallel.
        
        Args:
            device_list: List of all devices
            
        Returns:
            Dictionary with keys 'energy', 'co2', 'door' containing respective data
        """
        # Check if we have any supported devices
        if not self._has_supported_devices(device_list):
            _LOGGER.debug("No devices support special sensor data, skipping all requests")
            return {"energy": {}, "co2": {}, "door": {}}
        
        # Fetch all data types in parallel for efficiency
        _LOGGER.debug("Fetching all special sensor data in parallel")
        
        energy_task = self.get_energy_data(device_list)
        co2_task = self.get_co2_data(device_list)
        door_task = self.get_door_data(device_list)
        
        energy_data, co2_data, door_data = await asyncio.gather(
            energy_task, co2_task, door_task, return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(energy_data, Exception):
            _LOGGER.error("Energy data fetch failed: %s", energy_data)
            energy_data = {}
        
        if isinstance(co2_data, Exception):
            _LOGGER.error("CO2 data fetch failed: %s", co2_data)
            co2_data = {}
        
        if isinstance(door_data, Exception):
            _LOGGER.error("Door data fetch failed: %s", door_data)
            door_data = {}
        
        return {
            "energy": energy_data,
            "co2": co2_data,
            "door": door_data
        }
    
    def get_cached_energy_data(self, device_gwid: str) -> Optional[Dict[str, Any]]:
        """Get cached energy data for a specific device."""
        return self._energy_cache.get(device_gwid)
    
    def get_cached_co2_data(self, device_gwid: str) -> Optional[Dict[str, Any]]:
        """Get cached CO2 data for a specific device."""
        return self._co2_cache.get(device_gwid)
    
    def get_cached_door_data(self, device_gwid: str) -> Optional[Dict[str, Any]]:
        """Get cached door data for a specific device."""
        return self._door_cache.get(device_gwid)
    
    def clear_cache(self):
        """Clear all cached data."""
        self._energy_cache.clear()
        self._co2_cache.clear()
        self._door_cache.clear()
        self._last_energy_fetch = None
        self._last_co2_fetch = None
        self._last_door_fetch = None
        self._last_failed_fetch = None
        _LOGGER.debug("Report service cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            "energy_devices": len(self._energy_cache),
            "co2_devices": len(self._co2_cache),
            "door_devices": len(self._door_cache),
            "last_energy_fetch": self._last_energy_fetch,
            "last_co2_fetch": self._last_co2_fetch,
            "last_door_fetch": self._last_door_fetch,
        }