"""Token manager - specialized for authentication and token lifecycle handling"""
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from .api_client import ApiClient
from ..api_constants import APP_TOKEN, API_ENDPOINTS
from ..exceptions import (
    PanasonicRefreshTokenNotFound,
    PanasonicTokenExpired,
    PanasonicLoginFailed,
    PanasonicExceedRateLimit,
)
from ..base import ErrorHandler

_LOGGER = logging.getLogger(__name__)


class TokenManager:
    """Token lifecycle manager"""
    
    def __init__(self, api_client: ApiClient, account: str, password: str):
        """
        Initialize Token manager
        
        Args:
            api_client: API client instance
            account: User account
            password: User password
        """
        self._api_client = api_client
        self._account = account
        self._password = password
        
        # Token status
        self._refresh_token: Optional[str] = None
        self._cp_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._last_login_time: Optional[datetime] = None

        # Serializes login/refresh so concurrent callers don't overlap
        self._auth_lock = asyncio.Lock()

        # Statistics information
        self._login_count = 0
        self._refresh_count = 0
    
    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        return self._cp_token is not None and self._refresh_token is not None
    
    @property
    def cp_token(self) -> Optional[str]:
        """Get CP Token"""
        return self._cp_token
    
    @property
    def is_token_expired(self) -> bool:
        """Check if Token is expired"""
        if not self._token_expires_at:
            return True
        return datetime.now() > self._token_expires_at
    
    async def ensure_authenticated(self) -> str:
        """
        Ensure authenticated, automatically handle if not authenticated or token expired
        
        Returns:
            Valid CP Token
            
        Raises:
            PanasonicLoginFailed: Authentication failed
        """
        if not self.is_authenticated:
            _LOGGER.info("Not authenticated, starting login...")
            await self.login()
        elif self.is_token_expired:
            _LOGGER.info("Token about to expire, starting refresh...")
            try:
                await self.refresh_token()
            except (PanasonicTokenExpired, PanasonicRefreshTokenNotFound):
                _LOGGER.warning("Token refresh failed, re-login...")
                await self.login()
        
        return self._cp_token
    
    async def login(self) -> Dict[str, str]:
        """
        User login
        
        Returns:
            Dictionary containing token information
            
        Raises:
            PanasonicLoginFailed: Login failed
        """
        async with self._auth_lock:
            # Check if recently logged in (avoid too frequent logins). Under the
            # lock this also double-checks work done by a concurrent caller.
            if self._last_login_time:
                time_since_last_login = datetime.now() - self._last_login_time
                if time_since_last_login.total_seconds() < 30:  # Don't repeat login within 30 seconds
                    if self.is_authenticated:
                        _LOGGER.info("Recently logged in, using existing token")
                        return {
                            "refresh_token": self._refresh_token,
                            "cp_token": self._cp_token,
                        }

            _LOGGER.debug("Attempting login...")

            try:
                data = {
                    "MemId": self._account,
                    "PW": self._password,
                    "AppToken": APP_TOKEN
                }

                response = await self._api_client.request(
                    method="POST",
                    endpoint=API_ENDPOINTS["login"],
                    headers={},
                    data=data,
                    log=False  # Don't log sensitive information
                )

                # Validate response
                if not ErrorHandler.validate_response(response, ["RefreshToken", "CPToken"], "login response"):
                    raise PanasonicLoginFailed("Login response format error")

                # Update Token status
                self._refresh_token = response["RefreshToken"]
                self._cp_token = response["CPToken"]
                self._last_login_time = datetime.now()
                self._token_expires_at = datetime.now() + timedelta(hours=1)  # Assume 1 hour expiration
                self._login_count += 1

                _LOGGER.debug("Login successful")
                ErrorHandler.log_device_status("authentication system", "login_success", f"Login #{self._login_count}")

                return {
                    "refresh_token": self._refresh_token,
                    "cp_token": self._cp_token,
                }

            except (PanasonicLoginFailed, PanasonicExceedRateLimit, PanasonicTokenExpired) as e:
                # These are expected exceptions from lower layers, re-raise without additional logging
                raise
            except Exception as e:
                # Unexpected errors
                _LOGGER.error("Unexpected error during login: %s", e)
                raise PanasonicLoginFailed(f"Login failed: {str(e)}")
    
    async def refresh_token(self) -> Dict[str, str]:
        """
        Refresh Token
        
        Returns:
            Dictionary containing new token information
            
        Raises:
            PanasonicRefreshTokenNotFound: Refresh Token not found
            PanasonicTokenExpired: Token expired
        """
        _LOGGER.info("Attempting to refresh Token...")

        if self._refresh_token is None:
            raise PanasonicRefreshTokenNotFound("Refresh Token not found, re-login required")

        # Snapshot before contending for the lock so a concurrent refresh is detectable
        expiry_before_lock = self._token_expires_at

        async with self._auth_lock:
            # Double-check: another coroutine may have refreshed while we waited
            if self._token_expires_at != expiry_before_lock and not self.is_token_expired:
                _LOGGER.debug("Token already refreshed by another task, skipping")
                return {
                    "refresh_token": self._refresh_token,
                    "cp_token": self._cp_token,
                }

            try:
                data = {"RefreshToken": self._refresh_token}

                response = await self._api_client.request(
                    method="POST",
                    endpoint=API_ENDPOINTS["refresh_token"],
                    headers={},
                    data=data,
                    log=False  # Don't log sensitive information
                )

                # Validate response
                if not ErrorHandler.validate_response(response, ["RefreshToken", "CPToken"], "Token refresh response"):
                    raise PanasonicTokenExpired("Token refresh response format error")

                # Update Token status
                self._refresh_token = response["RefreshToken"]
                self._cp_token = response["CPToken"]
                self._token_expires_at = datetime.now() + timedelta(hours=1)
                self._refresh_count += 1

                _LOGGER.info("Token refresh successful")
                ErrorHandler.log_device_status("authentication system", "token_refreshed", f"Refresh #{self._refresh_count}")

                return {
                    "refresh_token": self._refresh_token,
                    "cp_token": self._cp_token,
                }

            except Exception as e:
                error_result = ErrorHandler.handle_api_error(e, "Token refresh")
                if error_result["status"] in ["token_expired", "login_failed"]:
                    raise PanasonicTokenExpired(f"Token refresh failed: {str(e)}")
                else:
                    raise
    
    def logout(self) -> None:
        """Logout, clear all Token information"""
        _LOGGER.debug("User logout")
        
        self._refresh_token = None
        self._cp_token = None
        self._token_expires_at = None
        self._last_login_time = None
        
        ErrorHandler.log_device_status("authentication system", "logout", "Clear authentication information")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers
        
        Returns:
            Header dictionary containing CP Token
            
        Raises:
            PanasonicLoginFailed: Not authenticated
        """
        if not self.is_authenticated:
            raise PanasonicLoginFailed("Not authenticated, cannot get authentication headers")
        
        return {"cptoken": self._cp_token}
    
    def get_device_auth_headers(self, device_id: str, gwid: Optional[str] = None) -> Dict[str, str]:
        """
        Get device operation authentication headers
        
        Args:
            device_id: Device ID
            gwid: Device GWID (optional)
            
        Returns:
            Header dictionary containing device authentication information
        """
        headers = self.get_auth_headers()
        headers["auth"] = device_id
        
        if gwid:
            headers["gwid"] = gwid
        
        return headers
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get Token status information
        
        Returns:
            Token status information dictionary
        """
        return {
            "is_authenticated": self.is_authenticated,
            "is_token_expired": self.is_token_expired,
            "last_login_time": self._last_login_time.isoformat() if self._last_login_time else None,
            "token_expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
            "login_count": self._login_count,
            "refresh_count": self._refresh_count,
        }
    
    def __repr__(self) -> str:
        """String representation"""
        status = "authenticated" if self.is_authenticated else "unauthenticated"
        return f"TokenManager(account={self._account}, status={status})"