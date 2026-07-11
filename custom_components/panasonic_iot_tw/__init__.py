"""The Panasonic IoT TW integration."""
from __future__ import annotations

import logging

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_PROXY, CONF_UPDATE_INTERVAL, PLATFORMS
from .coordinator import PanasonicConfigEntry, PanasonicCoordinator
from .exceptions import PanasonicLoginFailed
from .services import SmartApp

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: PanasonicConfigEntry) -> bool:
    """Set up Panasonic IoT TW from a config entry."""
    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    proxy = entry.options.get(CONF_PROXY, "")

    session = async_get_clientsession(hass)

    smart_app = SmartApp(
        session=session,
        account=username,
        password=password,
        proxy=proxy or None,
    )

    _LOGGER.debug("Loading Panasonic devices...")

    try:
        # Enable initialization mode for faster setup
        smart_app.set_initialization_mode(True)
        await smart_app.login()
    except PanasonicLoginFailed as err:
        smart_app.set_initialization_mode(False)
        raise ConfigEntryAuthFailed(
            "Login to Panasonic service failed"
        ) from err
    except Exception as err:
        smart_app.set_initialization_mode(False)
        _LOGGER.error("Failed to connect to Panasonic service: %s", err)
        raise ConfigEntryNotReady from err

    coordinator = PanasonicCoordinator(hass, entry, smart_app)

    try:
        await coordinator.async_config_entry_first_refresh()
    finally:
        # Disable initialization mode after the first refresh completes
        smart_app.set_initialization_mode(False)

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: PanasonicConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant, entry: PanasonicConfigEntry
) -> None:
    """Reload the entry when its options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: PanasonicConfigEntry) -> bool:
    """Migrate old config entries to the current version."""
    if entry.version == 1:
        data = dict(entry.data)
        options = dict(entry.options)

        # Move proxy and update interval from data into options
        for key in (CONF_PROXY, CONF_UPDATE_INTERVAL):
            if key in data:
                options.setdefault(key, data.pop(key))

        hass.config_entries.async_update_entry(
            entry, data=data, options=options, version=2
        )
        _LOGGER.debug("Migrated config entry to version 2")

    return True
