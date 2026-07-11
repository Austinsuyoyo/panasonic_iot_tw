# Panasonic IoT TW - Home Assistant 整合

[![GitHub Release](https://img.shields.io/github/release/austinsuyoyo/panasonic_iot_tw.svg?style=flat-square)](https://github.com/austinsuyoyo/panasonic_iot_tw/releases)
[![License](https://img.shields.io/github/license/austinsuyoyo/panasonic_iot_tw.svg?style=flat-square)](LICENSE)
[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg?style=flat-square)](https://github.com/hacs/integration)

透過 Panasonic IoT TW API 控制 Panasonic 智慧家電的全功能 Home Assistant 自定義整合。此整合採用現代工廠模式架構，提供完整的設備管理和實體支援。

## 🚀 功能特色

### 支援設備

| 設備類型 | 實體數量 | 支援功能 |
|----------|----------|----------|
| **冷氣機** | 18+ 實體 | 溫度控制、風速、模式、定時器、nanoeX、ECONAVI |
| **冰箱** | 15 實體 | 溫度控制/監控、ECO 模式、nanoe、除霜、製冰 |
| **洗衣機** | 13 實體 | 狀態監控、行程控制、剩餘時間、位元狀態 |
| **烘乾機** | 11 實體 | 行程控制、狀態監控、剩餘時間、位元狀態 |
| **除濕機** | 14+ 實體 | 濕度控制、風速、定時器、水箱狀態 |
| **空氣清淨機** | 4+ 實體 | 風量控制、PM2.5 監控、nanoeX |
| **全熱交換器** | 3+ 實體 | 運轉模式、風量控制 |
| **智慧開關** | 1 實體 | 開關控制 |

### 進階功能

- 🏭 **工廠模式架構** - 現代設備創建和管理
- 🔄 **即時狀態更新** - 自動同步設備狀態
- 🎛️ **全面控制** - 完整存取設備功能和設定
- 📊 **能耗監控** - 每月能耗追蹤
- 🌡️ **多重感測器** - 溫度、濕度、PM2.5 等
- ⏱️ **格式化時間顯示** - 智慧時間格式化 (如："2小時5分鐘")
- 🔢 **位元狀態** - 工程資訊的個別二進位感測器
- 🌐 **雙語支援** - 英文和繁體中文標籤
- 🛡️ **強健錯誤處理** - 完善的速率限制和重試機制

## 📋 系統需求

- **Home Assistant** 2023.1 或更新版本
- **Python** 3.10 或更新版本
- **Panasonic IoT TW 帳號** - 已註冊設備的有效帳號
- **網路連線** - 連接到 Panasonic 伺服器的網際網路連線 (`https://ems2.panasonic.com.tw/api`)

## 🔧 安裝方式

### 方法一：HACS (推薦)

1. **安裝 HACS** (如尚未安裝)
2. **新增自定義儲存庫**：
   - 前往 HACS → 整合 → ⋮ → 自定義儲存庫
   - 新增 `https://github.com/austinsuyoyo/panasonic_iot_tw`
   - 選擇類別：「整合」
3. **安裝整合**：
   - 搜尋「Panasonic IoT TW」
   - 點擊「安裝」
4. **重新啟動 Home Assistant**

### 方法二：手動安裝

1. **下載檔案**：
   ```bash
   cd /config/custom_components/
   git clone https://github.com/austinsuyoyo/panasonic_iot_tw.git
   ```

2. **複製整合**：
   ```bash
   cp -r panasonic_iot_tw/custom_components/panasonic_iot_tw ./
   ```

3. **重新啟動 Home Assistant**

## ⚙️ 設定說明

### 基本設定

1. **新增整合**：
   - 前往設定 → 裝置與服務
   - 點擊「新增整合」
   - 搜尋「Panasonic IoT TW」

2. **輸入憑證**：
   - **使用者名稱**：您的 Panasonic IoT TW 電子信箱
   - **密碼**：您的 Panasonic IoT TW 密碼
   - **代理伺服器** (選用)：HTTP 代理伺服器 (如需要)

3. **設定選項**：
   - **更新間隔**：設備狀態重新整理頻率 (預設：180 秒)

## 🏠 設備整合

### 冰箱 (15 個實體)

**溫度感測器 (3個):**
- 冷凍室溫度顯示 (-40~40°C)
- 冷藏室溫度顯示 (-39~40°C)
- 微凍結室溫度顯示 (-39~40°C)

**模式感測器 (4個):**
- 新鮮急凍結模式 (通常/冷卻/急冷/急凍)
- 冬季模式 (未啟動/啟動中/可啟動)
- 購物模式 (未啟動/啟動中/可啟動)
- 外出模式 (未啟動/啟動中/可啟動)

**二進位感測器 (3個):**
- ECO 狀態 (通常/運作中)
- 除霜狀態 (通常/除霜中)
- nanoe 狀態 (通常/運作中)

**開關控制 (2個):**
- 製冰停止控制 (停止/啟動)
- 快速製冰控制 (停止/啟動)

**溫度設定 (3個):**
- 冷凍庫溫度設定 (弱/中/強)
- 冷藏庫溫度設定 (弱/中/強)
- 微凍結室溫度設定 (弱/中/強)

### 洗衣機 (13 個實體)

**時間感測器 (2個):**
- 洗衣殘時間 (格式化："2小時5分鐘")
- 預約殘時間 (格式化小時顯示)

**狀態感測器 (2個):**
- 運轉情報 (待機中/動作中/預約中/終了/異常)
- 行程別訊息 (標準/快洗/大件行程/等)

**位元二進位感測器 (8個):**
- 工程資訊 0x34：預洗(128)、洗衣(64)、洗清(32)、脫水(16)
- 工程資訊 0x64：預洗(1024)、洗衣(64)、洗清(32)、脫水(16)

**控制二進位感測器 (1個):**
- 遠端控制允許 (不允許/允許)

### 烘乾機 (11 個實體)

**時間感測器 (2個):**
- 乾衣殘時間 (格式化："2小時5分鐘")
- 預約殘時間 (格式化小時顯示)

**狀態感測器 (2個):**
- 運轉情報 (待機中/動作中/預約中/終了/異常)
- 行程別訊息 (20+ 專業行程)

**位元二進位感測器 (6個):**
- 工程資訊 0x34：乾衣(8)、送風(4)、鬆柔冷卻(2)
- 乾衣模式參數 0x64：乾衣(8)、送風(4)、鬆柔冷卻(2)

**控制二進位感測器 (1個):**
- 遠端控制允許 (不允許/允許)

## 🏗️ 架構

### 現代工廠模式

此整合使用工廠模式進行設備特定的實體創建：

```
panasonic_iot_tw/
├── base/                    # 基礎架構
│   ├── device_base.py      # BaseDevice 抽象類別
│   └── status_reader.py    # 狀態讀取功能
├── devices/                # 設備實作
│   ├── device_factory.py  # DeviceFactory 模式
│   ├── refrigerator.py     # 15 個實體
│   ├── washing_machine.py  # 13 個實體
│   ├── dryer.py           # 11 個實體
│   └── ...
├── services/               # 核心業務邏輯
│   ├── smart_app.py       # 主要服務協調器
│   ├── api_client.py      # HTTP API 通訊
│   └── ...
└── platforms/              # Home Assistant 平台
    ├── sensor.py          # PanasonicTimeSensor, PanasonicStatusSensor
    ├── binary_sensor.py   # PanasonicBitwiseBinarySensor
    └── ...
```

### 核心元件

- **DeviceFactory**：使用工廠模式創建設備實例
- **BaseDevice**：具有實體創建介面的抽象基礎類別
- **自定義感測器**：時間格式化、狀態映射、位元運算
- **服務層**：具有速率限制的 API 通訊

## 🔧 故障排除

### 常見問題

#### 設備創建錯誤
```
ERROR: property 'device_data' of 'Device' object has no setter
```
**解決方案**：確保您使用的是具有 BaseDevice 屬性設定器的最新版本。

#### 未建立實體
```
INFO: Integration loaded but no entities appear
```
**解決方案：**
- 檢查支援設備清單中的設備相容性
- 驗證設備在 Panasonic IoT TW 應用程式中為線上狀態
- 檢查日誌中的設備類型錯誤
- 重新啟動 Home Assistant 整合

#### API 速率限制
```
WARNING: API request rate limit exceeded
```
**解決方案：**
- 將更新間隔增加至 300+ 秒
- 等待速率限制重設 (5-10 分鐘)

### 除錯記錄

在 `configuration.yaml` 中啟用詳細記錄：

```yaml
logger:
  logs:
    custom_components.panasonic_iot_tw: debug
```

## 🤝 貢獻

### 貢獻者與致謝

此專案建立在以下優秀作品的基礎上：

- **[PhantasWeng](https://github.com/PhantasWeng/panasonic_smart_app)** - 原始 Panasonic Smart App 整合基礎
- **[osk2](https://github.com/osk2/panasonic_smart_app)** - 額外改進和設備支援

特別感謝這些先驅者，讓這個綜合整合成為可能。

## 🔗 相似專案

以下是一些其他您可能會覺得有用的 Panasonic Home Assistant 整合：

- **[PhantasWeng/panasonic_smart_app](https://github.com/PhantasWeng/panasonic_smart_app)** - 原始 Panasonic Smart App 整合，提供基本設備支援
- **[osk2/panasonic_smart_app](https://github.com/osk2/panasonic_smart_app)** - 增強版本，支援更多設備類型和功能
- **[tsunglung/panasonic_ems2](https://github.com/tsunglung/panasonic_ems2)** - 替代的 Panasonic EMS2 整合方法

### 開發

1. **複製儲存庫**：
   ```bash
   git clone https://github.com/austinsuyoyo/panasonic_iot_tw.git
   cd panasonic_iot_tw
   ```

2. **設定環境**：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements-dev.txt
   ```

3. **執行測試**：
   ```bash
   python -m pytest tests/ -v
   ```

### 程式碼標準

- 需要 **Python 3.10+** 相容性
- 所有公開函數需要 **型別提示**
- 整個程式碼庫使用 **英文註解**
- 設備創建使用 **工廠模式**
- 平台分離的 **實體導向架構**

## 📜 授權

此專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 檔案。

## 📞 支援

### 取得協助

- **問題回報**：[GitHub Issues](https://github.com/austinsuyoyo/panasonic_iot_tw/issues)
- **討論**：[GitHub Discussions](https://github.com/austinsuyoyo/panasonic_iot_tw/discussions)
- **Home Assistant 社群**：[社群論壇](https://community.home-assistant.io/)

### 錯誤回報

回報錯誤時，請包含：

1. **Home Assistant 版本**
2. **整合版本**
3. **設備型號和類型**
4. **錯誤日誌** (已遮蔽個人資訊)
5. **重現步驟**

---

## ⚠️ 免責聲明

此為**非官方**整合。Panasonic 及相關標誌為松下電器產業株式會社（Panasonic Corporation）的註冊商標。本專案與 Panasonic 公司無任何正式關聯或隸屬關係。

本專案依原樣提供，不提供任何形式的保證。使用者需自行承擔使用本整合的風險。

---

**為 Home Assistant 社群用❤️製作**