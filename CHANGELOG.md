# Changelog

All notable changes to this integration are documented here.
中文說明在每個版本的第二段。

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versions follow the calendar scheme `YYYY.M.PATCH` used by Home Assistant.

## [Unreleased]

## [2026.7.2] - 2026-07-20

### Fixed

- A transient authentication failure no longer disables the integration.
  The cloud's auth endpoints share the nightly instability of its report
  API, and a single failed login used to raise a permanent
  re-authentication prompt that Home Assistant never retries. Reauth is now
  requested only when authentication keeps failing — three or more attempts
  spanning at least 30 minutes, outside the 00:00–08:00 window — and every
  other failure is retried automatically.

**暫時性認證失敗不再癱瘓整合。** Panasonic 雲端的認證端點在夜間偶發拒絕,
先前單次登入失敗就會觸發「重新驗證」並停止自動重試(實測造成 3.5 天停擺,
即使密碼根本沒變)。現在只有在維護窗以外、連續失敗 3 次以上且跨 30 分鐘,
才會要求重新驗證;其餘情況自動重試、恢復後自癒。

## [2026.7.1] - 2026-07-14

### Fixed

- Statistics sensors (energy, CO₂, door openings) no longer refresh inside
  the report API's nightly 00:00–08:00 maintenance window. The daily refresh
  now runs after 08:00, a failed fetch backs off 30 minutes instead of
  retrying every poll, and an empty response can no longer overwrite a good
  cache.
- Added the one-click HACS install button, fixed the license badge rendering
  inside HACS, and included the MIT licence file in the release.

**夜間統計資料異常。** 報表 API(能源/碳足跡/開門統計)在台灣時間
00:00–08:00 有維護窗會回錯誤;每日更新改為 08:00 後執行、失敗改 30 分鐘退避、
空回應不再覆蓋有效快取。README 另補上 HACS 一鍵安裝按鈕與 MIT 授權檔。

## [2026.7.0] - 2026-07-11

First public release. 首次公開發佈。

### Added

- Reauthentication flow: a changed password prompts re-authentication
  instead of retrying silently.
- Reconfigure flow: account, password and proxy are editable from the
  integration menu without deleting the entry.
- Diagnostics download, with credentials, gateway identifiers and
  coordinates redacted.
- Brand icon shipped inside the integration, displayed natively on Home
  Assistant 2026.3 and later.

### Changed

- Config entry schema v2: the proxy and update interval moved to the entry
  options, so values entered at setup actually apply. Existing entries
  migrate automatically.
- Entity availability is read live each poll, so devices going offline are
  reflected immediately and a cloud outage marks entities unavailable
  instead of leaving stale values on screen.
- Select and enum sensor states are stable English slugs, translated for
  display; the Chinese UI text is unchanged.

### Fixed

- The options flow no longer crashes when opened.
- A control command that fails now raises a visible error instead of
  silently doing nothing.
- Tokens are never written to the debug log, and concurrent refreshes are
  serialised behind a lock.

**首次公開發佈。** 修復必定崩潰的選項流程,新增重新驗證/重新設定流程、
診斷下載與內建品牌圖示;設定項升級為 v2(proxy 與更新間隔改放 options 並自動
遷移),實體可用性改為即時讀取,狀態值改用穩定 slug 並透過翻譯顯示中文;
指令失敗會在 UI 顯示錯誤,token 不再寫入除錯記錄。

[Unreleased]: https://github.com/Austinsuyoyo/panasonic_iot_tw/compare/v2026.7.2...HEAD
[2026.7.2]: https://github.com/Austinsuyoyo/panasonic_iot_tw/releases/tag/v2026.7.2
[2026.7.1]: https://github.com/Austinsuyoyo/panasonic_iot_tw/releases/tag/v2026.7.1
[2026.7.0]: https://github.com/Austinsuyoyo/panasonic_iot_tw/releases/tag/v2026.7.0
