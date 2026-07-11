"""Unit tests for config entry migration (v1 -> v2)."""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.panasonic_iot_tw import async_migrate_entry
from custom_components.panasonic_iot_tw.const import (
    CONF_PROXY,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)


async def test_migrate_v1_moves_proxy_and_interval_to_options(hass):
    """v1 entries move proxy/update_interval from data into options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "username": "user@example.com",
            "password": "secret",
            CONF_PROXY: "http://proxy:8080",
            CONF_UPDATE_INTERVAL: 240,
        },
        version=1,
    )
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True

    assert entry.version == 2
    # Credentials remain in data; proxy/interval move to options
    assert entry.data == {"username": "user@example.com", "password": "secret"}
    assert entry.options[CONF_PROXY] == "http://proxy:8080"
    assert entry.options[CONF_UPDATE_INTERVAL] == 240
