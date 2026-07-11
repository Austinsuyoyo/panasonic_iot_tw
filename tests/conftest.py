"""Test configuration for Panasonic IoT TW integration."""
import sys
import os
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import AsyncMock, Mock, patch
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


# 為 integration 測試允許網路連接
@pytest.fixture(scope="session")
def socket_enabled():
    """允許 socket 連接（覆蓋 pytest-homeassistant 的設定）"""
    return True


def pytest_runtest_setup(item):
    """在執行測試前的設定 - 允許 integration 測試使用網路"""
    # 檢查是否是 integration 測試
    if "integration" in str(item.fspath):
        # 允許網路連接
        if hasattr(item.config, "_socket_allow_hosts"):
            # 允許所有 host
            item.config._socket_allow_hosts = None


# Import project modules
from custom_components.panasonic_iot_tw.services.api_client import ApiClient
from custom_components.panasonic_iot_tw.services.token_manager import TokenManager
from custom_components.panasonic_iot_tw.services.smart_app import SmartApp
from custom_components.panasonic_iot_tw.api_constants import API_ENDPOINTS, API_METHODS, APP_TOKEN
from custom_components.panasonic_iot_tw.exceptions import (
    PanasonicDeviceOffline,
    PanasonicLoginFailed,
    PanasonicTokenExpired,
    PanasonicExceedRateLimit,
)

@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator keyed by device_id."""
    coordinator = Mock(spec=DataUpdateCoordinator)
    coordinator.last_update_success = True
    coordinator.data = {
        "test_device_1": {
            "device_id": "test_device_1",
            "nickname": "Test AC",
            "device_type": 1,
            "model": "Test Model",
            "version": "1.0.0",
            "available": True,
            "status": {
                "0x00": 1,  # Power on
                "0x01": 2,  # Fan level
                "0x02": 25, # Target temperature
            },
        }
    }
    coordinator.async_add_listener = Mock()
    coordinator.async_remove_listener = Mock()
    return coordinator

@pytest.fixture
def mock_smartapp():
    """Create a mock SmartApp client."""
    smartapp = AsyncMock()
    smartapp.login.return_value = True
    smartapp.get_devices.return_value = [
        {
            "device_id": "test_device_1",
            "nickname": "Test AC",
            "device_type": 1,
            "model": "Test Model",
            "version": "1.0.0"
        }
    ]
    smartapp.get_device_status.return_value = {
        "0x00": 1,  # Power on
        "0x01": 2,  # Fan level
        "0x02": 25, # Target temperature
    }
    return smartapp

@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.data = {}
    hass.config_entries = Mock()
    return hass


# Add pytest options for API testing
def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--live-api",
        action="store_true",
        default=False,
        help="Run API tests with live API calls (requires credentials)"
    )
    parser.addoption(
        "--mock-api",
        action="store_true",
        default=True,
        help="Run API tests in mock mode (default)"
    )


@pytest.fixture(scope="session")
def api_mode(request):
    """Determine API testing mode from command line arguments."""
    if request.config.getoption("--live-api"):
        return "live"
    return "mock"


# API Usage Test Session Class
class ApiUsageTestSession:
    """Test session for API usage testing with authentication management."""

    def __init__(self, account: str, password: str, proxy: Optional[str] = None, mock_mode: bool = True):
        """
        Initialize test session.

        Args:
            account: Panasonic IoT TW account
            password: Panasonic IoT TW password
            proxy: Optional proxy configuration
            mock_mode: Whether to use mock responses or real API calls
        """
        self.account = account
        self.password = password
        self.proxy = proxy
        self.mock_mode = mock_mode
        self.session = None
        self.smartapp = None
        self.api_client = None
        self.token_manager = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()

        if self.mock_mode:
            # Create mock components
            self.api_client = Mock(spec=ApiClient)
            self.token_manager = Mock(spec=TokenManager)
            self.smartapp = Mock(spec=SmartApp)
            self._setup_mock_responses()
        else:
            # Create real components
            self.api_client = ApiClient(self.session, self.proxy)
            self.token_manager = TokenManager(self.api_client, self.account, self.password)
            self.smartapp = SmartApp(self.session, self.account, self.password, self.proxy)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session and not self.mock_mode:
            await self.session.close()

    def _setup_mock_responses(self):
        """Setup mock responses for API endpoints."""

        # Mock successful login response
        self.token_manager.login = AsyncMock(return_value={
            "refresh_token": "mock_refresh_token_12345",
            "cp_token": "mock_cp_token_67890"
        })

        # Mock successful token refresh
        self.token_manager.refresh_token = AsyncMock(return_value={
            "refresh_token": "mock_refresh_token_new",
            "cp_token": "mock_cp_token_new"
        })

        # Mock device list response
        self.smartapp.get_devices = AsyncMock(return_value=[
            {
                "Auth": "device_auth_1",
                "GWID": "gateway_id_1",
                "NickName": "Test Air Conditioner",
                "DeviceType": "1",
                "Model": "CS-K25YA2"
            },
            {
                "Auth": "device_auth_2",
                "GWID": "gateway_id_2",
                "NickName": "Test Refrigerator",
                "DeviceType": "2",
                "Model": "NR-F503HPX"
            }
        ])

        # Mock API client request method
        async def mock_request(method, endpoint, headers=None, params=None, data=None, **kwargs):
            """Mock API request with realistic responses."""

            # Extract endpoint name from URL
            endpoint_name = None
            for name, url in API_ENDPOINTS.items():
                if endpoint == url:
                    endpoint_name = name
                    break

            if not endpoint_name:
                raise ValueError(f"Unknown endpoint: {endpoint}")

            # Return appropriate mock response based on endpoint
            return self._get_mock_response(endpoint_name, method, data)

        self.api_client.request = AsyncMock(side_effect=mock_request)
        self.api_client.request_with_retry = AsyncMock(side_effect=mock_request)

    def _get_mock_response(self, endpoint_name: str, method: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate mock response for specific endpoint."""

        responses = {
            "login": {
                "RefreshToken": "mock_refresh_token_12345",
                "CPToken": "mock_cp_token_67890",
                "StateMsg": "Success"
            },
            "get_devices": [
                {
                    "Auth": "device_auth_1",
                    "GWID": "gateway_id_1",
                    "NickName": "Test Air Conditioner",
                    "DeviceType": "1",
                    "Model": "CS-K25YA2"
                }
            ],
            "get_device_info": {
                "DeviceInfo": {
                    "DeviceType": "1",
                    "Model": "CS-K25YA2",
                    "Version": "1.0.0",
                    "Auth": "device_auth_1"
                },
                "StateMsg": "Success"
            },
            "get_info": {
                "UserInfo": {
                    "Account": self.account,
                    "Email": f"{self.account}@example.com",
                    "RegisteredDevices": 2
                },
                "StateMsg": "Success"
            },
            "get_device_overview": {
                "DeviceStatus": [
                    {
                        "Auth": "device_auth_1",
                        "Status": "Online",
                        "LastUpdate": "2024-12-19 10:30:00"
                    }
                ],
                "StateMsg": "Success"
            },
            "refresh_token": {
                "RefreshToken": "mock_refresh_token_new",
                "CPToken": "mock_cp_token_new",
                "StateMsg": "Success"
            }
        }

        return responses.get(endpoint_name, {"StateMsg": "Mock response not implemented"})

    async def test_endpoint(self, endpoint_name: str, method: str = None, data: Optional[Dict] = None,
                          headers: Optional[Dict] = None, expect_error: bool = False) -> Dict[str, Any]:
        """
        Test a specific API endpoint.

        Args:
            endpoint_name: Name of the endpoint to test
            method: HTTP method (if not specified, uses default from API_METHODS)
            data: Request data
            headers: Request headers
            expect_error: Whether to expect an error response

        Returns:
            API response data
        """
        if endpoint_name not in API_ENDPOINTS:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")

        endpoint_url = API_ENDPOINTS[endpoint_name]

        # Determine HTTP method
        if method is None:
            method = API_METHODS.get(endpoint_name, "POST")

        # Add authentication headers if needed
        if headers is None:
            headers = {}

        if endpoint_name != "login" and not self.mock_mode:
            # Add authentication for non-login endpoints
            auth_headers = await self._get_auth_headers()
            headers.update(auth_headers)

        try:
            if self.mock_mode:
                response = await self.api_client.request(method, endpoint_url, headers=headers, data=data)
            else:
                response = await self.api_client.request_with_retry(method, endpoint_url, headers=headers, data=data)

            if expect_error:
                pytest.fail(f"Expected error for endpoint {endpoint_name}, but got success response")

            return response

        except Exception as e:
            if not expect_error:
                pytest.fail(f"Unexpected error for endpoint {endpoint_name}: {e}")
            raise

    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if self.mock_mode:
            return {"cptoken": "mock_cp_token_67890"}
        else:
            await self.token_manager.ensure_authenticated()
            return self.token_manager.get_auth_headers()


# API Usage Test Fixtures
@pytest.fixture
def mock_credentials():
    """Provide mock credentials for testing."""
    return {
        "account": "test_account@example.com",
        "password": "test_password_123",
        "proxy": None
    }


@pytest.fixture
def real_credentials():
    """Provide real credentials from environment variables."""
    account = os.getenv("PANASONIC_ACCOUNT")
    password = os.getenv("PANASONIC_PASSWORD")
    proxy = os.getenv("PANASONIC_PROXY")

    if not account or not password:
        pytest.skip("Real credentials not available (PANASONIC_ACCOUNT and PANASONIC_PASSWORD required)")

    return {
        "account": account,
        "password": password,
        "proxy": proxy
    }


@pytest.fixture
def mock_test_session(mock_credentials, api_mode):
    """Create a test session based on API mode."""
    mock_mode = api_mode == "mock"
    if mock_mode:
        return ApiUsageTestSession(
            account=mock_credentials["account"],
            password=mock_credentials["password"],
            proxy=mock_credentials["proxy"],
            mock_mode=True
        )
    else:
        # For live mode, we need real credentials
        account = os.getenv("PANASONIC_ACCOUNT")
        password = os.getenv("PANASONIC_PASSWORD")
        proxy = os.getenv("PANASONIC_PROXY")

        if not account or not password:
            pytest.skip("Live API mode requires PANASONIC_ACCOUNT and PANASONIC_PASSWORD")

        return ApiUsageTestSession(
            account=account,
            password=password,
            proxy=proxy,
            mock_mode=False
        )


@pytest.fixture
def real_test_session(real_credentials):
    """Create a real test session (requires environment variables)."""
    return ApiUsageTestSession(
        account=real_credentials["account"],
        password=real_credentials["password"],
        proxy=real_credentials["proxy"],
        mock_mode=False
    )


@pytest.fixture
def api_endpoints():
    """Provide all API endpoints for testing."""
    return API_ENDPOINTS


@pytest.fixture
def api_methods():
    """Provide HTTP methods for each endpoint."""
    return API_METHODS


@pytest.fixture
def sample_device_data():
    """Provide sample device data for testing."""
    return [
        {
            "Auth": "device_auth_1",
            "GWID": "gateway_id_1",
            "NickName": "Test Air Conditioner",
            "DeviceType": "1",
            "Model": "CS-K25YA2"
        },
        {
            "Auth": "device_auth_2",
            "GWID": "gateway_id_2",
            "NickName": "Test Refrigerator",
            "DeviceType": "2",
            "Model": "NR-F503HPX"
        },
        {
            "Auth": "device_auth_3",
            "GWID": "gateway_id_3",
            "NickName": "Test Washing Machine",
            "DeviceType": "3",
            "Model": "NA-VX8000L"
        }
    ]


@pytest.fixture
def sample_error_responses():
    """Provide sample error responses for testing."""
    return {
        "invalid_credentials": {
            "StateMsg": "Invalid username or password"
        },
        "token_expired": {
            "StateMsg": "This CPToken has expired"
        },
        "device_offline": {
            "StateMsg": "deviceOffline"
        },
        "rate_limited": {
            "StateMsg": "System detected your current excessive usage"
        }
    }


# Test utilities
class APITestHelpers:
    """Helper methods for API testing."""

    @staticmethod
    def validate_response_structure(response: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that response contains required fields."""
        for field in required_fields:
            if field not in response:
                return False
        return True

    @staticmethod
    def validate_success_response(response: Dict[str, Any]) -> bool:
        """Validate that response indicates success."""
        state_msg = response.get("StateMsg", "")
        return "Success" in state_msg or not state_msg or state_msg == ""

    @staticmethod
    def validate_error_response(response: Dict[str, Any]) -> bool:
        """Validate that response indicates an error."""
        state_msg = response.get("StateMsg", "")
        error_keywords = ["Error", "Failed", "Invalid", "expired", "offline", "excessive usage"]
        return any(keyword in state_msg for keyword in error_keywords)


@pytest.fixture
def api_helpers():
    """Provide API testing helper methods."""
    return APITestHelpers