# Panasonic IoT TW - Home Assistant 整合

[![GitHub Release](https://img.shields.io/github/release/austinsuyoyo/panasonic_iot_tw.svg?style=flat-square)](https://github.com/austinsuyoyo/panasonic_iot_tw/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://github.com/Austinsuyoyo/panasonic_iot_tw/blob/main/LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://github.com/hacs/integration)

> English version: [README.md](README.md)

透過 Panasonic 台灣雲端服務（`ems2.panasonic.com.tw`）控制 Panasonic 台灣智慧家電的
Home Assistant 自訂整合。使用您的 **Panasonic Smart App 帳號** 登入，即可把家電變成
Home Assistant 原生實體。本整合為 `cloud_polling`（雲端輪詢）類型。

## 支援設備

| 設備 | Home Assistant 平台 | 主要功能 |
|------|---------------------|----------|
| **冷氣機** | climate、sensor、switch、select、number、button | 溫度／模式／風量／擺風、nanoeX、ECONAVI、急速、自體淨、定時器、室內外溫度、PM2.5 |
| **除濕機** | humidifier、sensor、binary_sensor、switch、select、number、button | 目標濕度、運轉模式、風向設定、水箱滿水、nanoe、PM2.5、開／關機定時 |
| **冰箱** | sensor、binary_sensor、switch、select | 冷凍／冷藏／微凍結溫度、新鮮急凍結／冬季／購物／外出模式、ECO、除霜、nanoe、製冰、能耗／碳足跡／開門次數感測器 |
| **洗衣機** | sensor、binary_sensor | 運轉情報、行程別訊息、剩餘時間、各階段工程資訊位元、遠端控制允許 |
| **烘乾機** | sensor、binary_sensor | 運轉情報、行程別訊息、剩餘時間、各階段工程資訊位元、遠端控制允許 |
| **全熱交換器（ERV）** | sensor、select | 運轉模式、風量設定 |
| **空氣清淨機** | sensor、switch | 風量、nanoeX、PM2.5 |
| **智慧開關** | switch | 開／關 |

啟用的平台：`climate`、`humidifier`、`sensor`、`binary_sensor`、`switch`、`select`、
`number`、`button`。

## 系統需求

- **Home Assistant** — 建議使用 **2026.3 或更新版本**，整合內建的品牌圖示才會原生
  顯示；較舊版本仍可正常運作，只是不會顯示圖示。
- **Panasonic Smart App 帳號**，且已註冊設備。
- 可連線到 `https://ems2.panasonic.com.tw` 的 **網際網路連線**。

## 安裝方式

### HACS（推薦）

[![在您的 Home Assistant 中開啟 HACS 並顯示此儲存庫。](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Austinsuyoyo&repository=panasonic_iot_tw&category=integration)

點上方按鈕一鍵加入,或手動操作:

1. 在 HACS 中前往 **整合 → ⋮ → 自訂儲存庫**。
2. 新增 `https://github.com/Austinsuyoyo/panasonic_iot_tw`，類別選擇 **整合
   （Integration）**。
3. 搜尋 **Panasonic IoT TW**，安裝後重新啟動 Home Assistant。

### 手動安裝

1. 將本儲存庫的 `custom_components/panasonic_iot_tw` 複製到 Home Assistant 的
   `config/custom_components/` 目錄。
2. 重新啟動 Home Assistant。

## 設定說明

1. 前往 **設定 → 裝置與服務 → 新增整合**，搜尋 **Panasonic IoT TW**。
2. 使用您的 **Panasonic Smart App 帳號**（電子信箱 + 密碼）登入。同一個表單也可
   選填 HTTP 代理伺服器與更新間隔。
3. 設定完成後，隨時可從整合卡片的 **「設定」** 按鈕調整選項：
   - **更新間隔** — 設備輪詢頻率，可設定 60–3600 秒（預設 **180 秒**）。
   - **代理伺服器** — 選填的 HTTP proxy。

### 重新驗證（Reauth）

當您的 Panasonic 密碼變更、儲存的憑證失效時，Home Assistant 會在整合卡片上跳出
**重新驗證** 提示，讓您輸入新密碼，而不會用錯誤的憑證持續靜默重試。

### 重新設定（Reconfigure）

不需刪除重加，即可修改帳號／密碼／代理伺服器：開啟整合卡片的 **⋮ 選單 →
重新設定（Reconfigure）**。若更改帳號，設定項會自動跟隨新帳號。

## v2026.7.0 新功能

本次為發佈前的重大改版，重點如下：

- **設定項結構升級為 v2** — 代理伺服器與更新間隔改放在設定項的 **options**（整合
  卡片上的 **「設定」** 按鈕）。舊的 v1 設定會在升級時 **自動遷移**，無需手動處理。
- **選項流程修復** — 更新間隔／代理伺服器的變更現在可正常套用並重新載入設定項，
  更新間隔會驗證在 60–3600 秒。
- **重新驗證流程** — 密碼變更時觸發 HA 重新驗證提示，取代原本的靜默重試迴圈。
- **重新設定流程** — 可從整合選單編輯帳號／密碼／代理伺服器。
- **即時可用性** — 設備上／下線會立即反映。雲端服務中斷時，實體會被標示為
  **不可用（unavailable）**，而不是顯示過期的舊資料。
- **失敗的指令會顯示為錯誤** — 控制指令失敗時，會在 UI 上跳出明確錯誤，而不是
  靜默沒有反應。
- **診斷資料下載**（已遮蔽敏感資訊）— 請見 [問題回報](#問題回報)。
- **內建品牌圖示** — 圖示隨整合封裝在
  `custom_components/panasonic_iot_tw/brand/`，在 Home Assistant **2026.3+**
  會原生顯示。

## 故障排除

### 沒有出現任何實體
- 確認設備類型在上方支援清單中。
- 確認設備在 Panasonic Smart App 中為線上狀態。
- 檢查日誌中的設備類型錯誤，並重新載入整合。

### 速率限制／更新緩慢
- 從 **「設定」** 按鈕調高更新間隔（例如 300 秒以上）。

### 除錯記錄

```yaml
logger:
  logs:
    custom_components.panasonic_iot_tw: debug
```

### 問題回報

回報問題時，請附上 **診斷資料** 下載檔：在整合卡片上點 **⋮ → 下載診斷資訊
（Download diagnostics）**。輸出內容已遮蔽敏感資訊（移除憑證與 token），並包含設定項
與設備狀態，能大幅加快除錯。也請一併提供您的 Home Assistant 版本、整合版本與設備型號。

## 開發

```bash
# 單元測試（離線，不需要憑證）
./venv/bin/pytest tests/unit
# 或先建立乾淨的環境：
pip install -r tests/requirements.txt
```

整合測試會連線 **真實的** Panasonic API，需透過環境變數提供有效憑證
（見 `tests/integration/`）：

```bash
export PANASONIC_ACCOUNT='your_account@example.com'
export PANASONIC_PASSWORD='your_password'
export PANASONIC_PROXY='http://proxy:port'   # 選填
```

請使用專用的測試帳號，且切勿將憑證 commit 進版控。

## 致謝

本專案建立在以下作品之上：

- **[PhantasWeng/panasonic_smart_app](https://github.com/PhantasWeng/panasonic_smart_app)** — 原始的 Panasonic Smart App 整合。
- **[osk2/panasonic_smart_app](https://github.com/osk2/panasonic_smart_app)** — 額外的設備支援與改進。

## 相似專案

- [PhantasWeng/panasonic_smart_app](https://github.com/PhantasWeng/panasonic_smart_app)
- [osk2/panasonic_smart_app](https://github.com/osk2/panasonic_smart_app)
- [tsunglung/panasonic_ems2](https://github.com/tsunglung/panasonic_ems2)

## 授權

MIT — 詳見 [LICENSE](LICENSE)。

---

## ⚠️ 免責聲明

此為 **非官方** 整合，與 **Panasonic 無任何關聯，亦未受其背書或贊助**。「Panasonic」
及相關標誌為其各自所有者（Panasonic Holdings Corporation）之商標。本軟體依原樣提供，
不提供任何形式的保證；使用者需自行承擔使用風險。
