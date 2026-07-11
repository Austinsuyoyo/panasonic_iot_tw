"""The Panasonic IoT TW integration."""
import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .services import SmartApp
from .const import (
    DATA_COORDINATOR,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    CONF_PROXY,
    CONF_UPDATE_INTERVAL,
    DEFAULT_NAME,
    PLATFORMS,
    DEVICE_STATUS_CODES,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Panasonic IoT TW from a config entry."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})

    username = entry.data.get(CONF_USERNAME)
    password = entry.data.get(CONF_PASSWORD)
    proxy = entry.options.get(CONF_PROXY, "")
    
    session = async_get_clientsession(hass)
    
    # Create SmartApp client
    smart_app = SmartApp(
        session=session,
        account=username,
        password=password,
        proxy=proxy if proxy else None
    )
    
    _LOGGER.info("Loading your Panasonic devices...")

    try:
        # Enable initialization mode for faster setup
        smart_app.set_initialization_mode(True)
        await smart_app.login()
    except Exception as e:
        # Disable initialization mode even if login fails
        smart_app.set_initialization_mode(False)
        _LOGGER.error(f"Failed to login to Panasonic service: {e}")
        raise ConfigEntryNotReady from e

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            _LOGGER.debug("Updating device info...")
            data = await smart_app.get_device_with_info(DEVICE_STATUS_CODES)
            _LOGGER.debug(f"Coordinator received data with {len(data)} devices")
            for key, device in data.items():
                device_name = device.get("nickname", "Unknown")
                device_type = device.get("device_type", "Unknown")
                available = device.get("available", False)
                _LOGGER.debug(f"Device {key}: {device_name} (type={device_type}, available={available})")
            return data
        except Exception as exc:
            _LOGGER.error(f"Failed while updating device status: {exc}")
            raise UpdateFailed(f"Error communicating with API: {exc}") from exc

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DEFAULT_NAME,
        update_method=async_update_data,
        update_interval=timedelta(
            seconds=entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        ),
    )

    # Store smart_app in coordinator for platform access
    coordinator.smart_app = smart_app

    # Initial data fetch with faster initialization mode
    await coordinator.async_config_entry_first_refresh()
    
    # Disable initialization mode after setup is complete
    smart_app.set_initialization_mode(False)

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    # Forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.add_update_listener(async_reload_entry)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)