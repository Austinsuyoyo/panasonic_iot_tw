"""Diagnostics support for the Panasonic IoT TW integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .coordinator import PanasonicConfigEntry

# Keys that carry credentials or personally identifying information. This must
# cover both the config-entry data/options and the nested device dicts stored in
# the coordinator (both the processed keys and the raw API keys inside
# ``raw_data``). Key matching in ``async_redact_data`` is case sensitive, so the
# raw API spellings (e.g. ``GWID``, ``Auth``, ``LatLng``) are listed explicitly.
TO_REDACT = {
    # Config entry credentials.
    "username",
    "password",
    # Processed device identifiers.
    "device_id",
    "auth",
    "gwid",
    # Raw API identifiers / credentials.
    "Auth",
    "GWID",
    "GWID2",
    "CPToken",
    "cptoken",
    "RefreshToken",
    "refreshtoken",
    "refresh_token",
    "cp_token",
    # Location fields.
    "LatLng",
    "latlng",
    "lat",
    "lng",
    "Lat",
    "Lng",
    "City",
    "city",
    "Area",
    "area",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: PanasonicConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    # The coordinator data is keyed by device_id (a credential-derived
    # identifier). async_redact_data only redacts values, not mapping keys, so
    # re-key by a synthetic index to avoid leaking the id while keeping a dict
    # shape and preserving every device (the redacted device dict still carries
    # its non-sensitive ``nickname`` for identification).
    redacted_devices = {
        f"device_{index}": async_redact_data(device, TO_REDACT)
        for index, device in enumerate((coordinator.data or {}).values())
    }

    update_interval = coordinator.update_interval
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": (
                update_interval.total_seconds()
                if update_interval is not None
                else None
            ),
        },
        "data": redacted_devices,
    }
