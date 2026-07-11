# Panasonic IoT TW - Home Assistant 整合

[![GitHub Release](https://img.shields.io/github/release/austinsuyoyo/panasonic_iot_tw.svg?style=flat-square)](https://github.com/austinsuyoyo/panasonic_iot_tw/releases)
[![License](https://img.shields.io/github/license/austinsuyoyo/panasonic_iot_tw.svg?style=flat-square)](LICENSE)
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

**重新設定** 流程（不需刪除重加，即可從整合選單修改帳號／密碼／代理伺服器）正由
另一位開發者同步加入；合併後會出現在整合卡片選單中，與「設定」並列。

## v2026.7.0 新功能

本次為發佈前的重大改版，重點如下：

- **設定項結構升級為 v2** — 代理伺服器與更新間隔改放在設定項的 **options**（整合
  卡片上的 **「設定」** 按鈕）。舊的 v1 設定會在升級時 **自動遷移**，無需手動處理。
- **選項流程修復** — 更新間隔／代理伺服器的變更現在可正常套用並重新載入設定項，
  更新間隔會驗證在 60–3600 秒。
- **重新驗證流程** — 密碼變更時觸發 HA 重新驗證提示，取代原本的靜默重試迴圈。
- **重新設定流程** — 可從選單編輯帳號／密碼／代理伺服器（同步加入中，見上文）。
- **即時可用性** — 設備上／下線會立即反映。雲端服務中斷時，實體會被標示為
  **不可用（unavailable）**，而不是顯示過期的舊資料。
- **失敗的指令會顯示為錯誤** — 控制指令失敗時，會在 UI 上跳出明確錯誤，而不是
  靜默沒有反應。
- **診斷資料下載**（已遮蔽敏感資訊）— 請見 [問題回報](#問題回報)。
- **內建品牌圖示** — 圖示隨整合封裝在
  `custom_components/panasonic_iot_tw/brand/`，在 Home Assistant **2026.3+**
  會原生顯示。
- **⚠️ 破壞性變更：實體狀態值改變** — 詳見下節。

## ⚠️ 破壞性變更 — select 與列舉型 sensor 的狀態值

**`select` 實體與列舉型 `sensor` 實體的原始狀態值（raw state），已由中文字串改為
穩定的英文 slug。** Home Assistant 介面仍會透過 `zh-Hant` 翻譯顯示中文，但只要您的
**自動化、腳本或模板是比對「原始」狀態值** 對照舊的中文字串，就必須改用新的 slug。

範例 — 原本這樣寫的自動化：

```yaml
condition:
  - condition: state
    entity_id: sensor.washing_machine_operation_status
    state: "動作中"          # 舊值 — 已不再符合
```

必須改為：

```yaml
condition:
  - condition: state
    entity_id: sensor.washing_machine_operation_status
    state: "running"        # 新的 slug
```

### 對照表（常用值）

| 類別 | 舊的原始狀態值 | 新的原始狀態值 |
|------|----------------|----------------|
| 運轉情報（洗衣機／烘乾機） | 不顯示 | `not_displayed` |
| 運轉情報（洗衣機／烘乾機） | 待機中 | `standby` |
| 運轉情報（洗衣機／烘乾機） | 動作中 | `running` |
| 運轉情報（洗衣機／烘乾機） | 預約中 | `reserved` |
| 運轉情報（洗衣機／烘乾機） | 終了 | `finished` |
| 運轉情報（洗衣機／烘乾機） | 異常 | `error` |
| 冰箱溫度設定（冷凍／冷藏／微凍結） | 弱 | `low` |
| 冰箱溫度設定 | 中 | `medium` |
| 冰箱溫度設定 | 強 | `high` |
| 除濕機運轉模式 | 自動 | `auto` |
| 除濕機運轉模式 | 連續除濕 | `continuous` |
| 除濕機運轉模式 | 衣物乾燥 | `clothes_drying` |
| 除濕機運轉模式 | 清淨 | `purify` |
| 除濕機風向設定 | 停止 | `stop` |
| 除濕機風向設定 | 上下擺動 | `swing` |
| 除濕機風向設定 | 水平 | `horizontal` |
| 除濕機風向設定 | 向上 | `up` |
| 除濕機風向設定 | 向下 | `down` |
| 全熱交換器運轉模式 | 停止 | `stop` |
| 全熱交換器運轉模式 | 自動 | `auto` |
| 全熱交換器運轉模式 | 低速 | `low` |
| 全熱交換器運轉模式 | 中速 | `medium` |
| 全熱交換器運轉模式 | 高速 | `high` |
| 全熱交換器運轉模式 | 換氣 | `ventilation` |
| 全熱交換器風量設定 | 停止 | `stop` |
| 全熱交換器風量設定 | 低速 | `low` |
| 全熱交換器風量設定 | 中速 | `medium` |
| 全熱交換器風量設定 | 高速 | `high` |

<details>
<summary>洗衣機／烘乾機「行程別訊息」完整 slug 對照（清單較長）</summary>

**烘乾機行程別訊息**（`sensor.*_cycle_message`）

| 舊的原始狀態值 | 新的原始狀態值 |
|----------------|----------------|
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

**洗衣機行程別訊息**（`sensor.*_cycle_message`）

| 舊的原始狀態值 | 新的原始狀態值 |
|----------------|----------------|
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
