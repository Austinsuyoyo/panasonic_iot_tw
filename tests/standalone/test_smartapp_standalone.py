#!/usr/bin/env python3
"""Standalone test for SmartApp functionality."""
import asyncio
import sys
import os
from pathlib import Path
import pytest

# Add the custom component path to sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from custom_components.panasonic_iot_tw.services.smart_app import SmartApp

@pytest.mark.asyncio
async def test_smartapp_connection():
    """Test SmartApp connection without Home Assistant."""
    print("Testing SmartApp standalone functionality...")
    
    from unittest.mock import Mock
    
    # Create mock session
    mock_session = Mock()
    
    # Initialize SmartApp with required parameters
    smartapp = SmartApp(
        session=mock_session,
        account="test_user",
        password="test_password"
    )
    
    # Test without real credentials (mock test)
    print("✓ SmartApp initialized successfully")
    
    # Test API client initialization
    assert smartapp._api_client is not None
    print("✓ API client initialized")
    
    # Test token manager initialization  
    assert smartapp._token_manager is not None
    print("✓ Token manager initialized")
    
    # Test device service initialization
    assert smartapp._device_service is not None
    print("✓ Device service initialized")
    
    print("All standalone tests passed!")

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling without network calls."""
    from custom_components.panasonic_iot_tw.exceptions import PanasonicAPIError, PanasonicAuthError
    
    # Test exception creation
    api_error = PanasonicAPIError("Test API error")
    assert str(api_error) == "Test API error"
    print("✓ PanasonicAPIError works correctly")
    
    auth_error = PanasonicAuthError("Test auth error")
    assert str(auth_error) == "Test auth error"
    print("✓ PanasonicAuthError works correctly")

if __name__ == "__main__":
    print("Running Panasonic IoT TW standalone tests...")
    
    try:
        asyncio.run(test_smartapp_connection())
        asyncio.run(test_error_handling())
        print("\n🎉 All standalone tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)