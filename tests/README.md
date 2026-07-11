# Panasonic IoT TW 測試套件

簡潔的測試框架，支援 venv 和 pytest，專為 Panasonic IoT TW Home Assistant 整合設計。

## 🚀 快速開始

### 1. 建立虛擬環境
```bash
cd /path/to/panasonic_iot_tw
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

### 2. 安裝依賴
```bash
# 安裝測試依賴
pip install -r tests/requirements.txt
```

### 3. 執行測試
```bash
# 進入測試目錄
cd tests/

# 執行所有測試
pytest

# 執行特定測試
pytest unit/test_devices/ -v
pytest unit/test_base/ -v
pytest standalone/ -v
```

## 📁 測試結構

```
tests/
├── README.md                    # 本文檔
├── pytest.ini                   # pytest 配置
├── conftest.py                  # 共用測試配置
├── requirements.txt             # 測試依賴
│
├── unit/                        # 單元測試（Mock）
│   ├── test_base/
│   │   └── test_error_handler.py
│   └── test_devices/
│       ├── test_air_conditioner.py
│       ├── test_dryer.py
│       ├── test_washing_machine.py
│       ├── test_device_factory.py
│       └── test_device_factory_simple.py
│
├── integration/                 # 真實 API 測試（需憑證）
│   ├── README.md
│   └── test_real_api.py
│
└── standalone/                  # 獨立測試
    └── test_smartapp_standalone.py
```

## 🧪 測試類型

### 單元測試 (unit/)
測試個別組件和功能：

```bash
# 測試設備實現
pytest unit/test_devices/ -v

# 測試錯誤處理
pytest unit/test_base/test_error_handler.py -v

# 測試服務層
pytest unit/test_services/ -v
```

### 獨立測試 (standalone/)
不依賴 Home Assistant 的核心功能測試：

```bash
pytest standalone/test_smartapp_standalone.py -v
```

### 真實 API 測試 (integration/)
需要真實 Panasonic IoT API 憑證的整合測試。

**⚠️ 當前狀態**：由於 `pytest-homeassistant-custom-component` 的 socket 阻擋限制，目前**無法透過 pytest** 執行真實 API 測試。

**當前解決方案**：使用獨立測試腳本

```bash
# 設定環境變數
export PANASONIC_ACCOUNT='your_account@example.com'
export PANASONIC_PASSWORD='your_password'

# 執行真實 API 測試（獨立腳本）
python tests/test_direct_api.py
```

**未來整合**：等待 [PR #218](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/pull/218) 合併後，可透過 pytest 執行：
```bash
pytest -m live_api -v
```

詳細說明請見 `integration/README.md`

## 🔧 測試覆蓋範圍

### 📊 測試統計
- **設備測試**: air_conditioner (22), dryer (19), washing_machine (18), device_factory (15+9)
- **基礎組件**: error_handler (51)
- **獨立測試**: smartapp_standalone (2)
- **總計**: 133 個測試通過

### 測試功能
- ✅ **單元測試**: 個別組件功能驗證
- ✅ **設備測試**: 各種設備實現測試
- ✅ **錯誤處理**: 完整的錯誤處理機制測試
- ✅ **非同步支援**: pytest-asyncio 整合
- ✅ **Mock 測試**: 完整的 mock 和 fixture 支援

## 🔒 環境變數設定

對於需要真實 API 測試的工具：

```bash
export PANASONIC_ACCOUNT='your_account@example.com'
export PANASONIC_PASSWORD='your_password'
export PANASONIC_PROXY='http://proxy:port'  # 選用
```

## 🐛 故障排除

### 常見問題

**1. 導入錯誤**
```bash
# 確認在專案根目錄
pwd

# 確認虛擬環境已啟動
which python
```

**2. 缺少依賴**
```bash
pip install -r tests/requirements-minimal.txt
```

**3. 測試失敗**
```bash
# 詳細執行模式
pytest -v -s

# 只執行特定測試
pytest unit/test_devices/test_dryer.py::TestDryerDevice::test_device_initialization -v
```

## 📊 測試覆蓋率

- **設備測試**: air_conditioner (22), dryer (19), washing_machine (18), device_factory (24)
- **基礎組件**: error_handler (51)
- **獨立測試**: smartapp_standalone (2)
- **總計**: 133 個測試通過 ✅

## 🎯 添加新測試

創建新的設備測試範例：

```python
# tests/unit/test_devices/test_my_device.py
import pytest
from unittest.mock import Mock
from custom_components.panasonic_iot_tw.devices.my_device import MyDevice

class TestMyDevice:
    @pytest.fixture
    def mock_coordinator(self):
        coordinator = Mock()
        coordinator.data = {0: {"status": {"0x00": 1}}}
        return coordinator

    def test_device_initialization(self, mock_coordinator):
        device_data = {"device_id": "test_001", "nickname": "Test Device"}
        device = MyDevice(mock_coordinator, 0, device_data)
        assert device.device_id == "test_001"
```

---

**輕量級測試框架，適用於 venv + pytest 環境**

製作給 Panasonic IoT TW 社群 ❤️