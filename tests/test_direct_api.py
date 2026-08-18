#!/usr/bin/env python3
"""
Real API test script - standalone version

Why is this script needed?

Because pytest-homeassistant-custom-component forcibly enables socket
blocking, tests that require a real network connection cannot be run
through pytest.

This script can be run directly, without depending on pytest, avoiding
the socket restriction.

Future plan:
   Once https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/pull/218
   is merged, these tests will be folded into tests/integration/test_real_api.py,
   and this file can be deleted.

Usage:
  python tests/test_direct_api.py

Environment variables:
  PANASONIC_ACCOUNT - Panasonic account
  PANASONIC_PASSWORD - Panasonic password

Related documents:
  - tests/integration/README.md - full integration plan description
  - tests/integration/test_real_api.py - pytest-format tests (pending activation)
"""
import asyncio
import aiohttp
import os
import sys
from pathlib import Path

# Add the project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.panasonic_iot_tw.services.smart_app import SmartApp


class TestResults:
    """Test result statistics"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_pass(self, name):
        self.passed += 1
        self.tests.append((name, "PASSED"))
        print(f"  ✅ {name}")

    def add_fail(self, name, error):
        self.failed += 1
        self.tests.append((name, f"FAILED: {error}"))
        print(f"  ❌ {name}: {error}")

    def summary(self):
        print("\n" + "=" * 60)
        print(f"Test results: {self.passed} passed, {self.failed} failed")
        if self.failed > 0:
            print("\nFailed tests:")
            for name, status in self.tests:
                if status.startswith("FAILED"):
                    print(f"  - {name}: {status}")
        print("=" * 60)


async def test_login(smartapp, results):
    """Test 1: login functionality"""
    try:
        result = await smartapp.login()
        # login() returns a token dict or True
        assert result is not None and result is not False, f"Login failed, return value: {result}"
        assert smartapp._token_manager.cp_token is not None, "Token not obtained"
        results.add_pass("test_login")
        token = smartapp._token_manager.cp_token
        print(f"     Token: {token[:20]}...{token[-10:]}")
        return True
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        results.add_fail("test_login", str(e))
        print(f"\nDetailed error:\n{error_detail}")
        return False


async def test_get_devices(smartapp, results):
    """Test 2: retrieve device list"""
    try:
        devices = await smartapp.get_devices()
        assert isinstance(devices, list), "Device list has the wrong format"
        assert len(devices) >= 0, "Device count error"
        results.add_pass("test_get_devices")
        print(f"     Found {len(devices)} device(s)")
        return devices
    except Exception as e:
        results.add_fail("test_get_devices", str(e))
        return []


async def test_device_info(devices, results):
    """Test 3: verify device info"""
    if len(devices) == 0:
        results.add_pass("test_device_info (skipped - no devices)")
        return

    try:
        device = devices[0]
        assert "device_id" in device, "Missing device_id"
        assert "nickname" in device, "Missing nickname"
        assert "model" in device, "Missing model"
        results.add_pass("test_device_info")
        print(f"     Device: {device.get('nickname')} ({device.get('model')})")
    except Exception as e:
        results.add_fail("test_device_info", str(e))


async def main():
    """Run all tests"""
    account = os.getenv("PANASONIC_ACCOUNT")
    password = os.getenv("PANASONIC_PASSWORD")

    if not account or not password:
        print("❌ Error: please set the environment variables")
        print("   export PANASONIC_ACCOUNT='your_account@example.com'")
        print("   export PANASONIC_PASSWORD='your_password'")
        return False

    print("🧪 Panasonic IoT TW real API test")
    print("=" * 60)
    print(f"Account: {account}")
    print("=" * 60)

    results = TestResults()

    async with aiohttp.ClientSession() as session:
        smartapp = SmartApp(session, account, password)

        print("\nRunning tests:")

        # Test 1: login
        if not await test_login(smartapp, results):
            results.summary()
            return False

        # Test 2: get devices
        devices = await test_get_devices(smartapp, results)

        # Test 3: verify device info
        await test_device_info(devices, results)

        # Show device details
        if devices:
            print("\n" + "=" * 60)
            print("📱 Device details:")
            print("=" * 60)
            for i, device in enumerate(devices, 1):
                print(f"\nDevice {i}:")
                print(f"  ID: {device.get('device_id')}")
                print(f"  Name: {device.get('nickname')}")
                print(f"  Model: {device.get('model')}")
                print(f"  Type: {device.get('device_type')}")

    results.summary()
    return results.failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
