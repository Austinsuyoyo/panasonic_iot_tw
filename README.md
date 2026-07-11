# Panasonic IoT TW - Home Assistant Integration

[![GitHub Release](https://img.shields.io/github/release/austinsuyoyo/panasonic_iot_tw.svg?style=flat-square)](https://github.com/austinsuyoyo/panasonic_iot_tw/releases)
[![License](https://img.shields.io/github/license/austinsuyoyo/panasonic_iot_tw.svg?style=flat-square)](LICENSE)
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

A **Reconfigure** flow (change account / password / proxy from the integration
menu without deleting and re-adding the entry) is being added in parallel; once
merged it appears in the integration card's menu alongside Configure.

## What's new in v2026.7.0

This is a major pre-publication overhaul. Highlights:

- **Config entry schema v2** — the proxy and update interval now live in the
  entry **options** (the **Configure** button on the integration card). Existing
  v1 entries are **migrated automatically** on upgrade; no manual action needed.
- **Options flow fixed** — changing the update interval / proxy now works and
  reloads the entry. Update interval is validated to 60–3600 s.
- **Reauthentication flow** — password changes trigger an HA re-auth prompt
  instead of a silent retry loop.
- **Reconfigure flow** — account / password / proxy editable from the menu
  (being added concurrently, see above).
- **Live availability** — devices going offline / online are reflected
  immediately. During a cloud outage entities are marked **unavailable** rather
  than showing stale values.
- **Failed commands surface as errors** — a control command that fails now
  raises a visible error in the UI instead of silently doing nothing.
- **Diagnostics download** (redacted) — see [Reporting issues](#reporting-issues).
- **Bundled brand icon** — the icon ships inside
  `custom_components/panasonic_iot_tw/brand/` and displays natively on Home
  Assistant **2026.3+**.
- **⚠️ Breaking change: entity state values changed** — see below.

## ⚠️ Breaking change — select & enum-sensor state values

**Raw entity state values for `select` entities and enum `sensor` entities
changed from Chinese strings to stable English slugs.** The Home Assistant UI
still shows the Chinese text (via the `zh-Hant` translations), but any
**automation, script, or template that compares the _raw_ state** against the
old Chinese string must be updated to the new slug.

Example — an automation that previously used:

```yaml
condition:
  - condition: state
    entity_id: sensor.washing_machine_operation_status
    state: "動作中"          # OLD — no longer matches
```

must become:

```yaml
condition:
  - condition: state
    entity_id: sensor.washing_machine_operation_status
    state: "running"        # NEW slug
```

### Migration table (common values)

| Group | Old raw state | New raw state |
|-------|---------------|---------------|
| Operation status (washer & dryer) | 不顯示 | `not_displayed` |
| Operation status (washer & dryer) | 待機中 | `standby` |
| Operation status (washer & dryer) | 動作中 | `running` |
| Operation status (washer & dryer) | 預約中 | `reserved` |
| Operation status (washer & dryer) | 終了 | `finished` |
| Operation status (washer & dryer) | 異常 | `error` |
| Refrigerator temperature setting (freezer / fridge / partial-freeze) | 弱 | `low` |
| Refrigerator temperature setting | 中 | `medium` |
| Refrigerator temperature setting | 強 | `high` |
| Dehumidifier operation mode | 自動 | `auto` |
| Dehumidifier operation mode | 連續除濕 | `continuous` |
| Dehumidifier operation mode | 衣物乾燥 | `clothes_drying` |
| Dehumidifier operation mode | 清淨 | `purify` |
| Dehumidifier fan direction | 停止 | `stop` |
| Dehumidifier fan direction | 上下擺動 | `swing` |
| Dehumidifier fan direction | 水平 | `horizontal` |
| Dehumidifier fan direction | 向上 | `up` |
| Dehumidifier fan direction | 向下 | `down` |
| ERV operation mode | 停止 | `stop` |
| ERV operation mode | 自動 | `auto` |
| ERV operation mode | 低速 | `low` |
| ERV operation mode | 中速 | `medium` |
| ERV operation mode | 高速 | `high` |
| ERV operation mode | 換氣 | `ventilation` |
| ERV fan level | 停止 | `stop` |
| ERV fan level | 低速 | `low` |
| ERV fan level | 中速 | `medium` |
| ERV fan level | 高速 | `high` |

<details>
<summary>Full washer &amp; dryer cycle-message slugs (long)</summary>

**Dryer cycle message** (`sensor.*_cycle_message`)

| Old raw state | New raw state |
|---------------|---------------|
| 棉麻行程 | `cotton_linen` |
| 大件行程 | `large_items` |
| 自選行程 | `custom` |
| 高級衣物行程 | `premium_clothing` |
| 羊毛行程 | `wool` |
| 運動服行程 | `sportswear` |
| 羽绒衣行程 | `down_jacket` |
| 抑菌烘行程 | `antibacterial_dry` |
| nanoe™X-抑菌行程 | `nanoex_antibacterial` |
| nanoe™X-除臭行程 | `nanoex_deodorize` |
| nanoe™X-除蟎行程 | `nanoex_dust_mite` |
| nanoe™X-除皺行程 | `nanoex_dewrinkle` |
| nanoe™X-鬆柔行程 | `nanoex_softening` |
| nanoe™X-皮草保養行程 | `nanoex_fur_care` |
| 快烘行程 | `quick_dry` |
| 嬰兒衣物行程 | `baby_clothes` |
| 薄被行程 | `thin_quilt` |
| 合成纖維行程 | `synthetic_fiber` |
| 襯衫行程 | `shirts` |
| 混合行程 | `mixed` |
| 機能衣行程 | `functional_wear` |
| 牛仔行程 | `denim` |
| 浴巾行程 | `bath_towel` |
| 冷風清新行程 | `cool_air_refresh` |
| 工作/校服行程 | `work_school_uniform` |
| 溫風暖衣行程 | `warm_air` |

**Washing-machine cycle message** (`sensor.*_cycle_message`)

| Old raw state | New raw state |
|---------------|---------------|
| 標準 | `standard` |
| 浸泡 | `soak` |
| 快洗 | `quick_wash` |
| 槽洗淨 | `tub_clean` |
| 大件行程 | `large_items` |
| 除蟎 | `dust_mite_removal` |
| 自選 | `custom` |
| 高級衣物 | `premium_clothing` |
| 羊毛 | `wool` |
| 運動服 | `sportswear` |
| 羽绒衣 | `down_jacket` |
| 高溫抑菌 | `high_temp_antibacterial` |
| 節能洗 | `eco_wash` |
| 脫水 | `spin` |
| 合成纖維 | `synthetic_fiber` |
| 襯衫 | `shirts` |
| 混合洗 | `mixed` |
| 牛仔 | `denim` |

</details>

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
