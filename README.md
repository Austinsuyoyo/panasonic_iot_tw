# Panasonic IoT TW - Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/austinsuyoyo/panasonic_iot_tw.svg?style=flat-square)](https://github.com/austinsuyoyo/panasonic_iot_tw/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://github.com/hacs/integration)

> 中文說明請見 [README-zh.md](README-zh.md)。

A Home Assistant custom integration that controls Panasonic Taiwan smart
appliances through the Panasonic IoT TW cloud (`ems2.panasonic.com.tw`). It logs
in with your **Panasonic Smart App** account and exposes your appliances as
native Home Assistant entities. This is a `cloud_polling` integration.

## Supported Devices

| Device | Home Assistant platforms | Highlights |
|--------|--------------------------|------------|
| **Air Conditioner** | climate, sensor, switch, select, number, button | Temperature / mode / fan / swing, nanoeX, ECONAVI, turbo, self-clean, timers, indoor & outdoor temperature, PM2.5 |
| **Dehumidifier** | humidifier, sensor, binary_sensor, switch, select, number, button | Target humidity, operation mode, fan direction, tank-full, nanoe, PM2.5, on/off timers |
| **Refrigerator** | sensor, binary_sensor, switch, select | Freezer / fridge / partial-freeze temperature, fresh-freezing / winter / shopping / vacation modes, ECO, defrost, nanoe, ice-making, energy / CO₂ / door-open sensors |
| **Washing Machine** | sensor, binary_sensor | Operation status, cycle message, remaining time, per-stage engineering-info bits, remote-control-allowed |
| **Dryer** | sensor, binary_sensor | Operation status, cycle message, remaining time, per-stage engineering-info bits, remote-control-allowed |
| **ERV (Energy Recovery Ventilator)** | sensor, select | Operation mode, fan level |
| **Air Purifier** | sensor, switch | Fan level, nanoeX, PM2.5 |
| **Smart Switch** | switch | On / off |

Enabled platforms: `climate`, `humidifier`, `sensor`, `binary_sensor`, `switch`,
`select`, `number`, `button`.

## Requirements

- **Home Assistant** — a recent release. **2026.3 or newer** is recommended so
  the integration's bundled brand icon is displayed natively; the integration
  still works on older versions, just without the icon.
- **Panasonic Smart App account** with registered devices.
- **Internet access** to `https://ems2.panasonic.com.tw`.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Austinsuyoyo&repository=panasonic_iot_tw&category=integration)

Click the button above, or manually:

1. In HACS, go to **Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/Austinsuyoyo/panasonic_iot_tw` and choose the
   category **Integration**.
3. Search for **Panasonic IoT TW**, install it, and restart Home Assistant.

### Manual

1. Copy `custom_components/panasonic_iot_tw` from this repository into your Home
   Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration** and search for
   **Panasonic IoT TW**.
2. Log in with your **Panasonic Smart App** account (email + password). You can
   optionally set an HTTP proxy and the update interval on the same form.
3. After setup, tune options at any time from the integration card's
   **Configure** button:
   - **Update interval** — device poll rate, configurable 60–3600 s (default
     **180 s**).
   - **Proxy** — optional HTTP proxy.

### Reauthentication

If your Panasonic password changes and the stored credentials stop working,
Home Assistant raises a **re-authentication** prompt on the integration card so
you can enter the new password, instead of silently retrying a bad login.

### Reconfigure

Change the account, password, or proxy without deleting and re-adding the
entry: open the integration card's **⋮ menu → Reconfigure**. If the username
changes, the entry follows the new account automatically.

## What's new in v2026.7.0

This is a major pre-publication overhaul. Highlights:

- **Config entry schema v2** — the proxy and update interval now live in the
  entry **options** (the **Configure** button on the integration card). Existing
  v1 entries are **migrated automatically** on upgrade; no manual action needed.
- **Options flow fixed** — changing the update interval / proxy now works and
  reloads the entry. Update interval is validated to 60–3600 s.
- **Reauthentication flow** — password changes trigger an HA re-auth prompt
  instead of a silent retry loop.
- **Reconfigure flow** — account / password / proxy editable from the
  integration menu.
- **Live availability** — devices going offline / online are reflected
  immediately. During a cloud outage entities are marked **unavailable** rather
  than showing stale values.
- **Failed commands surface as errors** — a control command that fails now
  raises a visible error in the UI instead of silently doing nothing.
- **Diagnostics download** (redacted) — see [Reporting issues](#reporting-issues).
- **Bundled brand icon** — the icon ships inside
  `custom_components/panasonic_iot_tw/brand/` and displays natively on Home
  Assistant **2026.3+**.

## Troubleshooting

### No entities appear
- Confirm the device type is in the supported list above.
- Confirm the devices are online in the Panasonic Smart App.
- Check the logs for device-type errors and restart the integration.

### Rate limiting / slow updates
- Raise the update interval (e.g. 300 s+) from the **Configure** button.

### Debug logging

```yaml
logger:
  logs:
    custom_components.panasonic_iot_tw: debug
```

### Reporting issues

When filing a bug, please attach the **diagnostics** download: on the
integration card go to **⋮ → Download diagnostics**. The output is redacted
(credentials and tokens removed) and captures the config entry and device
state, which greatly speeds up debugging. Also include your Home Assistant
version, the integration version, and the device model.

## Development

```bash
# Unit tests (offline, no credentials needed)
./venv/bin/pytest tests/unit
# or set up a fresh environment first:
pip install -r tests/requirements.txt
```

Integration tests hit the **real** Panasonic API and require valid credentials
supplied through environment variables (see `tests/integration/`):

```bash
export PANASONIC_ACCOUNT='your_account@example.com'
export PANASONIC_PASSWORD='your_password'
export PANASONIC_PROXY='http://proxy:port'   # optional
```

Use a dedicated test account and never commit credentials.

## Acknowledgments

This project builds on the work of:

- **[PhantasWeng/panasonic_smart_app](https://github.com/PhantasWeng/panasonic_smart_app)** — the original Panasonic Smart App integration.
- **[osk2/panasonic_smart_app](https://github.com/osk2/panasonic_smart_app)** — additional device support and improvements.

## Similar projects

- [PhantasWeng/panasonic_smart_app](https://github.com/PhantasWeng/panasonic_smart_app)
- [osk2/panasonic_smart_app](https://github.com/osk2/panasonic_smart_app)
- [tsunglung/panasonic_ems2](https://github.com/tsunglung/panasonic_ems2)

## License

MIT — see [LICENSE](LICENSE).

---

## ⚠️ Disclaimer

This is an **unofficial** integration and is **not affiliated with, endorsed by,
or sponsored by Panasonic**. "Panasonic" and related logos are trademarks of
their respective owner (Panasonic Holdings Corporation). The software is
provided as-is, without warranty; you assume all risk from using it.
