"""Pure HTTP API client - responsible only for HTTP request handling"""
import logging
import asyncio
from typing import Literal, Optional, Dict, Any
from http import HTTPStatus
from aiohttp import ClientTimeout

from ..api_constants import (
    USER_AGENT,
    REQUEST_TIMEOUT,
    MIN_SAFETY_DELAY,
    INIT_SAFETY_DELAY,
    RATE_LIMIT_BACKOFF_BASE,
    RATE_LIMIT_MAX_DELAY,
    EXCEPTION_MESSAGES,
    API_ENDPOINTS,
    APP_TOKEN,
)
from ..exceptions import (
    PanasonicDeviceOffline,
    PanasonicLoginFailed,
    PanasonicTokenExpired,
    PanasonicExceedRateLimit,
)
from ..base import ErrorHandler

_LOGGER = logging.getLogger(__name__)


class ApiClient:
    """Pure HTTP API client, responsible only for network request handling"""
    
    def __init__(self, session, proxy: Optional[str] = None):
        """
        Initialize API client
        
        Args:
            session: aiohttp session
            proxy: Proxy server configuration
        """
        self._session = session
        self._proxy = proxy
        self._request_counter = 0
        self._devices_cache = []  # Cache device list for error handling
        self._initialization_mode = False  # Track if in initialization phase
        self._last_request_time = 0  # Track timing for minimal delays
        self._rate_limit_until = 0  # Track when rate limiting ends
    
    def set_devices_cache(self, devices: list) -> None:
        """Set device cache for error message generation"""
        self._devices_cache = devices
    
    def set_initialization_mode(self, enabled: bool) -> None:
        """
        Set initialization mode to use faster timeouts during setup
        
        Args:
            enabled: Whether to enable initialization mode
        """
        self._initialization_mode = enabled
        _LOGGER.debug(f"Initialization mode {'enabled' if enabled else 'disabled'}")
    
    async def request(
        self,
        method: Literal["GET", "POST"],
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        log: bool = True,
        apply_delay: bool = True,
    ) -> Dict[str, Any]:
        """
        Send HTTP request
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            headers: Request headers
            params: URL parameters
            data: Request data
            log: Whether to log request information
            apply_delay: Whether to apply delay (to avoid rate limiting)
            
        Returns:
            API response data
            
        Raises:
            PanasonicDeviceOffline: Device offline
            PanasonicLoginFailed: Login failed
            PanasonicTokenExpired: Token expired
            PanasonicExceedRateLimit: Rate limit exceeded
        """
        # Smart delay logic: minimal delays with rate limiting awareness
        if apply_delay:
            import time
            current_time = time.time()
            
            # Check if we're still under rate limiting
            if current_time < self._rate_limit_until:
                remaining_wait = self._rate_limit_until - current_time
                _LOGGER.warning(f"Rate limited: waiting {remaining_wait:.1f} seconds")
                await asyncio.sleep(remaining_wait)
                
            # Minimal safety delay to be respectful to the API
            elif self._last_request_time > 0:
                time_since_last = current_time - self._last_request_time
                if self._initialization_mode:
                    min_delay = INIT_SAFETY_DELAY
                else:
                    min_delay = MIN_SAFETY_DELAY
                    
                if time_since_last < min_delay:
                    wait_time = min_delay - time_since_last
                    _LOGGER.debug(f"Safety delay: {wait_time:.1f}s ({'init' if self._initialization_mode else 'normal'} mode)")
                    await asyncio.sleep(wait_time)
            
            self._last_request_time = time.time()
        
        # Prepare request
        request_id = self._request_counter + 1
        self._request_counter = request_id
        
        if headers is None:
            headers = {}
        headers["user-agent"] = USER_AGENT
        
        if log:
            # Detailed logging for debugging (sanitize sensitive tokens)
            sanitized_headers = {k: ('***' if k in ['cptoken', 'auth'] else v) for k, v in headers.items()}
            _LOGGER.debug(
                f"Making #{request_id} request to {endpoint} with headers {sanitized_headers} "
                f"and data {data}, proxy: {self._proxy}"
            )
        
        try:
            # Send request with explicit ClientTimeout to override session defaults
            response = await self._session.request(
                method,
                url=endpoint,
                json=data,
                params=params,
                headers=headers,
                timeout=ClientTimeout(total=REQUEST_TIMEOUT),
                proxy=self._proxy,
            )
            
            # Process response
            return await self._process_response(response, request_id, headers, log)

        except (PanasonicLoginFailed, PanasonicExceedRateLimit, PanasonicTokenExpired, PanasonicDeviceOffline) as e:
            # These are business logic exceptions, re-raise them directly
            raise
        except Exception as e:
            # Only handle true connection errors
            return self._handle_connection_error(e, headers)
    
    async def _process_response(
        self, 
        response, 
        request_id: int, 
        headers: Dict[str, str], 
        log: bool
    ) -> Dict[str, Any]:
        """Process HTTP response"""
        if response.status == HTTPStatus.OK:
            return await self._handle_success_response(response, request_id, log)
        
        elif response.status == HTTPStatus.EXPECTATION_FAILED:
            return await self._handle_expectation_failed(response, headers)
        
        elif response.status == HTTPStatus.TOO_MANY_REQUESTS:
            raise PanasonicExceedRateLimit("API requests too frequent")
        
        else:
            await self._handle_error_response(response, request_id)
            return {}
    
    async def _handle_success_response(
        self,
        response,
        request_id: int,
        log: bool
    ) -> Dict[str, Any]:
        """Handle success response"""
        try:
            response_text = await response.text()
            if log:
                _LOGGER.debug(
                    f"Succeed to access #{request_id} API. Returned {response.status}: {response_text}"
                )
            # Parse JSON from text
            import json
            resp_data = json.loads(response_text)
            return resp_data
        except Exception as e:
            _LOGGER.warning(f"Failed to parse JSON response: {e}")
            return {}
    
    async def _handle_expectation_failed(
        self, 
        response, 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Handle 417 Expectation Failed response"""
        try:
            resp_data = await response.json()
        except Exception as e:
            # Get raw response text for debugging
            try:
                response_text = await response.text()
                _LOGGER.debug(f"Non-JSON response received: {response_text[:200]}...")
            except:
                response_text = "Unable to get response text"

            # Check for common error messages in plain text response
            if "帳號或密碼錯誤" in response_text or "帳號或密碼不正確" in response_text:
                raise PanasonicLoginFailed("Invalid username or password")

            # Check if it's rate limiting
            if "超量使用" in response_text or "rate" in response_text.lower():
                raise PanasonicExceedRateLimit("API requests too frequent")

            # Invalid CPToken or other parsing error
            raise PanasonicLoginFailed(f"Unable to parse API response: {response_text[:100]}")
        
        state_msg = resp_data.get("StateMsg", "")
        
        # Check device offline exceptions
        offline_exceptions = [
            EXCEPTION_MESSAGES["DEVICE_OFFLINE"],
            EXCEPTION_MESSAGES["DEVICE_NOT_RESPONDING"],
            EXCEPTION_MESSAGES["DEVICE_JP_INFO"],
            EXCEPTION_MESSAGES["DEVICE_JP_FAILED"],
        ]
        
        if state_msg in offline_exceptions:
            device_name = self._get_device_name_from_auth(headers.get("auth"))
            raise PanasonicDeviceOffline(
                f"Device '{device_name}' is offline or not responding (API message: {state_msg})"
            )
        
        elif state_msg == EXCEPTION_MESSAGES["INVALID_REFRESH_TOKEN"]:
            raise PanasonicTokenExpired("Token expired, re-authentication required")
        
        else:
            _LOGGER.error(f"API response error: {state_msg}")
            raise PanasonicLoginFailed(f"API response error: {state_msg}")
    
    async def _handle_error_response(self, response, request_id: int) -> None:
        """Handle error response"""
        response_text = await response.text()
        _LOGGER.error(
            f"Failed to access #{request_id} API. Returned {response.status}: {response_text}"
        )
    
    def _handle_connection_error(self, error: Exception, headers: Dict[str, str]) -> Dict[str, Any]:
        """Handle connection error"""
        auth = headers.get("auth")
        device_name = self._get_device_name_from_auth(auth) if auth else "device"
        raise PanasonicDeviceOffline(f"Cannot connect to '{device_name}': {str(error)}")
    
    def _get_device_name_from_auth(self, auth: Optional[str]) -> str:
        """Get device name by auth"""
        if not auth or not self._devices_cache:
            return "unknown device"
        
        for device in self._devices_cache:
            if device.get("Auth") == auth:
                return device.get("NickName", "unknown device")
        
        return "未知設備"
    
    async def request_with_retry(
        self,
        method: Literal["GET", "POST"],
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Request with retry mechanism
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            headers: Request headers
            params: URL parameters
            data: Request data
            max_retries: Maximum retry count
            retry_delay: Retry delay time
            
        Returns:
            API response data
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.request(
                    method=method,
                    endpoint=endpoint,
                    headers=headers,
                    params=params,
                    data=data,
                    log=attempt == 0,  # Log only on first attempt
                )
            except PanasonicExceedRateLimit as e:
                last_exception = e
                if attempt < max_retries:
                    # Smart rate limiting: set future rate limit period
                    import time
                    backoff_time = min(RATE_LIMIT_BACKOFF_BASE * (2 ** attempt), RATE_LIMIT_MAX_DELAY)
                    self._rate_limit_until = time.time() + backoff_time
                    
                    _LOGGER.warning(f"Rate limited! Setting backoff period: {backoff_time}s (attempt {attempt + 1})")
                    await asyncio.sleep(backoff_time)
                else:
                    break
            except PanasonicDeviceOffline as e:
                last_exception = e
                if attempt < max_retries:
                    _LOGGER.warning(f"Device offline (attempt {attempt + 1}), retrying in {retry_delay}s")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    break
            except (PanasonicTokenExpired, PanasonicLoginFailed):
                # These errors should not be retried, throw directly
                raise
        
        # All retries failed
        if last_exception:
            raise last_exception
        else:
            raise PanasonicDeviceOffline("Request failed, maximum retry count reached")
    
    async def post(self, endpoint: str, data: Any = None, headers: Optional[Dict[str, str]] = None, json: Any = None) -> Dict[str, Any]:
        """
        Send POST request - convenience method for ReportService
        
        Args:
            endpoint: API endpoint URL
            data: Request data (will be JSON encoded) - legacy parameter
            headers: Optional request headers
            json: Request data (will be JSON encoded) - preferred parameter
            
        Returns:
            API response data
        """
        # Support both 'data' and 'json' parameters for compatibility
        payload = json if json is not None else data
        return await self.request("POST", endpoint, headers=headers, data=payload)
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get request statistics"""
        return {
            "total_requests": self._request_counter,
            "cached_devices": len(self._devices_cache),
        }