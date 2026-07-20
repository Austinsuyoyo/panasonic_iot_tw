"""Data update coordinator for the Panasonic IoT TW integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

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

# The Panasonic cloud (including its auth endpoints) is unreliable between
# 00:00 and 08:00 local time — the backend's day runs 8 hours ahead. A single
# failed login at night must not be treated as bad credentials: HA never
# retries after ConfigEntryAuthFailed, so a transient blip would disable the
# integration until the user manually reauthenticates. Only escalate to
# reauth when auth keeps failing persistently outside that window.
AUTH_MAINTENANCE_END_HOUR = 8
AUTH_FAIL_MIN_COUNT = 3
AUTH_FAIL_MIN_DURATION = timedelta(minutes=30)


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
        self._auth_failure_count = 0
        self._first_auth_failure: Optional[datetime] = None
        update_interval = entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DEFAULT_NAME,
            update_interval=timedelta(seconds=update_interval),
        )

    def _classify_auth_failure(self, err: Exception) -> Exception:
        """Decide whether an auth error warrants reauth or a plain retry."""
        now = datetime.now()
        self._auth_failure_count += 1
        if self._first_auth_failure is None:
            self._first_auth_failure = now

        persistent = (
            self._auth_failure_count >= AUTH_FAIL_MIN_COUNT
            and now - self._first_auth_failure >= AUTH_FAIL_MIN_DURATION
        )
        in_maintenance_window = now.hour < AUTH_MAINTENANCE_END_HOUR

        if persistent and not in_maintenance_window:
            return ConfigEntryAuthFailed(
                f"Authentication with Panasonic service failed: {err}"
            )

        _LOGGER.warning(
            "Authentication error (attempt %d%s), will retry: %s",
            self._auth_failure_count,
            " during nightly maintenance window" if in_maintenance_window else "",
            err,
        )
        return UpdateFailed(f"Authentication error, retrying: {err}")

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
            raise self._classify_auth_failure(err) from err
        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with Panasonic service: {err}"
            ) from err

        self._auth_failure_count = 0
        self._first_auth_failure = None
        _LOGGER.debug("Coordinator received data with %d devices", len(data))
        return data
