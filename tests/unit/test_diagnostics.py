"""Unit tests for the Panasonic IoT TW diagnostics."""
from datetime import timedelta
from unittest.mock import Mock

import pytest

from custom_components.panasonic_iot_tw.const import CONF_PROXY, CONF_UPDATE_INTERVAL
from custom_components.panasonic_iot_tw.diagnostics import (
    async_get_config_entry_diagnostics,
)

REDACTED = "**REDACTED**"


def _entry_with_coordinator():
    """Build a config entry whose runtime_data is a coordinator with data."""
    coordinator = Mock()
    coordinator.last_update_success = True
    coordinator.update_interval = timedelta(seconds=180)
    coordinator.data = {
        "device_auth_1": {
            "device_id": "device_auth_1",
            "auth": "device_auth_1",
            "gwid": "gateway_id_1",
            "nickname": "Living Room AC",
            "model": "CS-K25YA2",
            "device_type": 1,
            "available": True,
            "status": {"0x00": 1},
            "raw_data": {
                "Auth": "device_auth_1",
                "GWID": "gateway_id_1",
                "NickName": "Living Room AC",
                "DeviceType": "1",
                "Model": "CS-K25YA2",
                "LatLng": "25.03,121.56",
                "City": "Taipei",
                "Area": "Xinyi",
            },
        }
    }

    entry = Mock()
    entry.data = {"username": "user@example.com", "password": "secret"}
    entry.options = {CONF_PROXY: "http://proxy:8080", CONF_UPDATE_INTERVAL: 180}
    entry.runtime_data = coordinator
    return entry


async def test_diagnostics_structure():
    """Diagnostics return the expected top-level structure."""
    entry = _entry_with_coordinator()

    result = await async_get_config_entry_diagnostics(Mock(), entry)

    assert set(result) == {"entry", "coordinator", "data"}
    assert set(result["entry"]) == {"data", "options"}
    assert result["coordinator"]["last_update_success"] is True
    assert result["coordinator"]["update_interval"] == 180.0
    # Non-sensitive fields survive.
    assert result["data"]["device_0"]["nickname"] == "Living Room AC"
    assert result["data"]["device_0"]["model"] == "CS-K25YA2"
    assert result["entry"]["options"][CONF_PROXY] == "http://proxy:8080"


async def test_diagnostics_redacts_credentials():
    """Credentials and identifiers never appear verbatim in the output."""
    entry = _entry_with_coordinator()

    result = await async_get_config_entry_diagnostics(Mock(), entry)

    dumped = str(result)
    for secret in (
        "secret",
        "user@example.com",
        "gateway_id_1",
        "device_auth_1",
        "25.03,121.56",
    ):
        assert secret not in dumped, f"{secret!r} leaked into diagnostics"

    # Specific redactions on both processed and raw keys.
    device = result["data"]["device_0"]
    assert device["gwid"] == REDACTED
    assert device["auth"] == REDACTED
    assert device["device_id"] == REDACTED
    assert device["raw_data"]["GWID"] == REDACTED
    assert device["raw_data"]["Auth"] == REDACTED
    assert device["raw_data"]["LatLng"] == REDACTED
    assert device["raw_data"]["City"] == REDACTED
    assert result["entry"]["data"]["password"] == REDACTED
    assert result["entry"]["data"]["username"] == REDACTED
