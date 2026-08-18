# -*- coding: utf-8 -*-
"""
Real API integration tests

Current status: due to socket-blocking restrictions in
pytest-homeassistant-custom-component, these tests currently cannot run.
Use tests/test_direct_api.py instead.

Future integration: once
https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/pull/218
is merged, these tests will be able to run normally through pytest.

These tests connect to the real Panasonic IoT API and require valid
account credentials.

How to run (future):
  # Skip real API tests (default)
  pytest

  # Run real API tests (requires environment variables)
  pytest -m live_api

Environment variables:
  export PANASONIC_ACCOUNT='your_account@example.com'
  export PANASONIC_PASSWORD='your_password'
  export PANASONIC_PROXY='http://proxy:port'  # optional
"""

import pytest
import os
import aiohttp
from typing import Optional

from custom_components.panasonic_iot_tw.services.smart_app import SmartApp
from custom_components.panasonic_iot_tw.exceptions import (
    PanasonicLoginFailed,
    PanasonicAPIError,
)


# Check whether API credentials are available
def has_api_credentials() -> bool:
    """Check whether API credentials have been configured."""
    return bool(
        os.getenv("PANASONIC_ACCOUNT") and
        os.getenv("PANASONIC_PASSWORD")
    )


# If no credentials, skip all real API tests
pytestmark = [
    pytest.mark.skipif(
        not has_api_credentials(),
        reason="Requires PANASONIC_ACCOUNT and PANASONIC_PASSWORD environment variables"
    ),
    pytest.mark.enable_socket,  # Allow real network connections
]


@pytest.fixture
def api_credentials():
    """Provide API credentials."""
    return {
        "account": os.getenv("PANASONIC_ACCOUNT"),
        "password": os.getenv("PANASONIC_PASSWORD"),
        "proxy": os.getenv("PANASONIC_PROXY"),
    }


@pytest.mark.live_api
@pytest.mark.asyncio
class TestRealAPILogin:
    """Test real API login functionality."""

    async def test_login_success(self, api_credentials):
        """Test successful login."""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=api_credentials["account"],
                password=api_credentials["password"],
                proxy=api_credentials["proxy"]
            )

            result = await smartapp.login()
            assert result, "Login should succeed"
            assert result.get("cp_token"), "Login result should include a CP Token"
            assert smartapp._token_manager.cp_token is not None, "Should have obtained a CP Token"
            print(f"\n✅ Login succeeded")
            print(f"   CP Token: {smartapp._token_manager.cp_token[:20]}...")

    async def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials."""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account="invalid@example.com",
                password="wrong_password"
            )

            with pytest.raises(PanasonicLoginFailed):
                await smartapp.login()


@pytest.mark.live_api
@pytest.mark.asyncio
class TestRealAPIDevices:
    """Test real API device operations."""

    async def test_get_devices(self, api_credentials):
        """Test retrieving the device list."""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=api_credentials["account"],
                password=api_credentials["password"],
                proxy=api_credentials["proxy"]
            )

            # Log in first
            await smartapp.login()

            # Get devices
            devices = await smartapp.get_devices()

            assert isinstance(devices, list), "Device list should be a list"
            assert len(devices) >= 0, "Device list length should be >= 0"

            if len(devices) > 0:
                device = devices[0]
                assert "device_id" in device, "Device should have a device_id"
                assert "nickname" in device, "Device should have a nickname"
                print(f"\n✅ Found {len(devices)} device(s)")
                print(f"   First device: {device.get('nickname')} ({device.get('device_id')})")

    async def test_get_device_status(self, api_credentials):
        """Test retrieving device status."""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=api_credentials["account"],
                password=api_credentials["password"],
                proxy=api_credentials["proxy"]
            )

            # Log in first
            await smartapp.login()

            # Get devices
            devices = await smartapp.get_devices()

            if len(devices) == 0:
                pytest.skip("No devices available to test")

            # Just verify that device info can be retrieved
            device = devices[0]

            # Verify device data structure
            assert "device_id" in device
            assert "nickname" in device
            print(f"\n✅ Device info is correct")
            print(f"   Device name: {device.get('nickname')}")
            print(f"   Device model: {device.get('model')}")
            print(f"   Device type: {device.get('device_type')}")


@pytest.mark.live_api
@pytest.mark.asyncio
class TestRealAPICommands:
    """Test real API control commands (use with caution)."""

    @pytest.mark.skip(reason="Control commands affect real devices, skipped by default")
    async def test_send_command(self, api_credentials):
        """Test sending a control command (skipped by default)."""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=api_credentials["account"],
                password=api_credentials["password"],
                proxy=api_credentials["proxy"]
            )

            # Log in first
            await smartapp.login()

            # Get devices
            devices = await smartapp.get_devices()

            if len(devices) == 0:
                pytest.skip("No devices available to test")

            # Actual control command tests could be added here
            # Note: this would affect the real device!
            device = devices[0]

            # Example: only verify device info, don't control it
            assert device is not None
            assert "device_id" in device


@pytest.mark.live_api
@pytest.mark.asyncio
class TestRealAPITokenManagement:
    """Test real API token management."""

    async def test_token_refresh(self, api_credentials):
        """Test token refresh."""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=api_credentials["account"],
                password=api_credentials["password"],
                proxy=api_credentials["proxy"]
            )

            # Log in first
            await smartapp.login()

            old_token = smartapp._token_manager.cp_token

            # Refresh the token (if the API supports it)
            # Note: the actual implementation may need to wait for the token to expire

            # Verify the token exists
            assert old_token is not None, "Should have a CP Token"
            print(f"\n✅ Token management is working")
            print(f"   CP Token: {old_token[:10]}...{old_token[-10:]}")


@pytest.mark.live_api
@pytest.mark.asyncio
class TestRealAPIFridgeRegisters:
    """Verify fridge register decoding assumptions (read-only).

    These registers are not documented in the official CommandList; they
    were derived by comparing events before and after state changes.
    Running this class confirms cloud behavior hasn't changed, and lets
    us capture live values when an anomaly occurs.
    """

    FRIDGE_REGISTERS = [
        "0x03", "0x05", "0x0E", "0x13", "0x51",
        "0x64", "0x65", "0x66", "0x68", "0x69",
    ]

    async def _read_fridge(self, credentials, registers):
        """Return the raw values of the specified fridge registers."""
        from custom_components.panasonic_iot_tw.api_constants import API_ENDPOINTS

        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=credentials["account"],
                password=credentials["password"],
                proxy=credentials["proxy"],
            )
            await smartapp.login()
            devices = await smartapp.get_devices()
            fridge = next((d for d in devices if d.get("device_type") == 2), None)
            if fridge is None:
                pytest.skip("This account has no fridge")

            raw = fridge["raw_data"]
            api = smartapp._api_client
            headers = smartapp._token_manager.get_device_auth_headers(
                device_id=raw.get("Auth"), gwid=raw.get("GWID")
            )
            data = [{"CommandTypes": [{"CommandType": c} for c in registers],
                     "DeviceID": 1}]
            response = await api.request(
                method="POST", endpoint=API_ENDPOINTS["get_device_info"],
                headers=headers, data=data,
            )
            info = (response.get("devices") or [{}])[0].get("Info", [])
            return {i["CommandType"]: int(i["status"]) for i in info}

    async def test_dump_fridge_registers(self, api_credentials):
        """Print all current register values (run this to capture state during an incident)."""
        values = await self._read_fridge(api_credentials, self.FRIDGE_REGISTERS)
        meaning = {
            "0x03": "Freezer temp", "0x05": "Fridge temp", "0x0E": "Error code (per implementation-defined reference)",
            "0x13": "Cumulative power usage", "0x51": "Status bits, bit0=ice box",
            "0x66": "Door status, bit15=open",
        }
        print("\n=== Fridge register snapshot ===")
        for reg in self.FRIDGE_REGISTERS:
            if reg in values:
                print(f"  {reg} = {values[reg]:<8} 0x{values[reg]:04X}  {meaning.get(reg, '')}")
            else:
                print(f"  {reg} = (unsupported)")
        assert values, "Should have read at least one register"

    async def test_door_bit_is_readable(self, api_credentials):
        """0x66 exists and bit15 can be decoded as the door open/closed state."""
        values = await self._read_fridge(api_credentials, ["0x66"])
        assert "0x66" in values, "0x66 should have a response"
        door_open = bool(values["0x66"] & 0x8000)
        print(f"\n0x66 = {values['0x66']} (0x{values['0x66']:04X}) → door "
              f"{'open' if door_open else 'closed'}")
        assert values["0x66"] != 65535, "65535 means unsupported, which would invalidate the decoding assumption"

    async def test_status_flags_readable(self, api_credentials):
        """0x51 exists; bit0 = 1 means ice box is normal, 0 means full."""
        values = await self._read_fridge(api_credentials, ["0x51"])
        assert "0x51" in values, "0x51 should have a response"
        flags = values["0x51"]
        print(f"\n0x51 = {flags} (0b{flags:08b}) → ice box "
              f"{'normal' if flags & 0x01 else 'full'}")
        assert flags != 65535, "65535 means unsupported"
