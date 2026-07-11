"""Data update coordinator for the Panasonic IoT TW integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL,
    DEVICE_STATUS_CODES,
)
from .exceptions import (
    PanasonicLoginFailed,
    PanasonicRefreshTokenNotFound,
    PanasonicTokenExpired,
)
from .services import SmartApp

_LOGGER = logging.getLogger(__name__)

PanasonicConfigEntry = ConfigEntry["PanasonicCoordinator"]


class PanasonicCoordinator(DataUpdateCoordinator[Dict[str, Dict[str, Any]]]):
    """Coordinator that owns the SmartApp client and polls device state."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: PanasonicConfigEntry,
        smart_app: SmartApp,
    ) -> None:
        """Initialize the coordinator."""
        self.smart_app = smart_app
        update_interval = entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DEFAULT_NAME,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> Dict[str, Dict[str, Any]]:
        """Fetch the latest device state from the Panasonic service."""
        _LOGGER.debug("Updating device info...")
        try:
            data = await self.smart_app.get_device_with_info(DEVICE_STATUS_CODES)
        except (
            PanasonicLoginFailed,
            PanasonicTokenExpired,
            PanasonicRefreshTokenNotFound,
        ) as err:
            raise ConfigEntryAuthFailed(
                f"Authentication with Panasonic service failed: {err}"
            ) from err
        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with Panasonic service: {err}"
            ) from err

        _LOGGER.debug("Coordinator received data with %d devices", len(data))
        return data
