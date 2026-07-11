# 真實 API 整合測試

這個目錄包含需要連接真實 Panasonic IoT API 的測試。

## ⚠️ 當前狀態：無法透過 pytest 執行

**重要**: 由於 `pytest-homeassistant-custom-component` 強制啟用 socket 阻擋，**目前無法透過 pytest 執行真實 API 測試**。

### 問題說明

`pytest-homeassistant-custom-component` 套件在 `pytest_runtest_setup()` hook 中強制執行：
```python
pytest_socket.socket_allow_hosts(["127.0.0.1"])
pytest_socket.disable_socket(allow_unix_socket=True)
```

這會阻擋所有外部網路連線，導致真實 API 測試失敗。

相關追蹤：
- [Issue #154](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/issues/154) - SocketBlockedError 問題
- [PR #218](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/pull/218) - **將 pytest-socket 改為可選依賴**

### 當前解決方案

使用獨立測試腳本 **`tests/test_direct_api.py`**：

```bash
# 設定環境變數
export PANASONIC_ACCOUNT='your_account@example.com'
export PANASONIC_PASSWORD='your_password'

# 執行真實 API 測試
python tests/test_direct_api.py
```

輸出範例：
```
🧪 Panasonic IoT TW 真實 API 測試
執行測試:
  ✅ test_login
     Token: XXXXXXXX-XXXX-XXXX-...
  ✅ test_get_devices
     找到 3 個裝置
  ✅ test_device_info
     裝置: Panasonic 冰箱 (NR-D611XGS)

測試結果: 3 passed, 0 failed
```

---

## 🔮 未來整合計畫

### 當 PR #218 合併後

一旦 [PR #218](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/pull/218) 合併，將 pytest-socket 改為可選依賴，這些測試就能透過 pytest 執行。

#### 整合步驟

1. **更新依賴**
   ```bash
   # requirements.txt
   pytest-homeassistant-custom-component>=0.14.0  # 假設版本
   ```

2. **配置 pytest**

   `integration/conftest.py` 已經準備好，使用 `@pytest.hookimpl(trylast=True)` 覆蓋 socket 限制：
   ```python
   from pytest_socket import enable_socket

   @pytest.hookimpl(trylast=True)
   def pytest_runtest_setup():
       enable_socket()  # 允許網路連接
   ```

3. **執行測試**
   ```bash
   # 執行真實 API 測試
   pytest -m live_api -v

   # 或執行所有測試（包含 mock 和真實 API）
   pytest
   ```

4. **遷移 test_direct_api.py**

   將獨立腳本的測試整合進 `test_real_api.py`，然後刪除 `test_direct_api.py`。

---

## 📋 測試文件狀態

### 當前文件

- ✅ **`tests/test_direct_api.py`** - 獨立腳本，可執行（3 個測試）
  - `test_login` - 登入功能
  - `test_get_devices` - 取得裝置列表
  - `test_device_info` - 驗證裝置資訊

- ⏸️ **`test_real_api.py`** - pytest 格式，因 socket 阻擋無法執行（6 個測試）
  - `TestRealAPILogin.test_login_success` - 登入成功
  - `TestRealAPILogin.test_login_with_invalid_credentials` - 錯誤憑證
  - `TestRealAPIDevices.test_get_devices` - 裝置列表
  - `TestRealAPIDevices.test_get_device_status` - 裝置狀態
  - `TestRealAPICommands.test_send_command` - 控制命令（skip）
  - `TestRealAPITokenManagement.test_token_refresh` - Token 刷新

---

## 🧪 執行測試（未來可用）

### 方式 1: 執行所有測試（包含真實 API）

```bash
cd tests/
pytest
```

### 方式 2: 只執行真實 API 測試

```bash
# 設定憑證
export PANASONIC_ACCOUNT='your_account@example.com'
export PANASONIC_PASSWORD='your_password'

# 執行測試
cd tests/
pytest -m live_api -v
```

### 方式 3: 執行特定測試

```bash
# 只測試登入
pytest integration/test_real_api.py::TestRealAPILogin -v

# 只測試裝置列表
pytest integration/test_real_api.py::TestRealAPIDevices::test_get_devices -v
```

### 方式 4: 排除真實 API 測試

```bash
pytest -m "not live_api" -v
```

## 📋 測試項目

### TestRealAPILogin - 登入測試
- ✅ `test_login_success` - 測試登入成功
- ✅ `test_login_with_invalid_credentials` - 測試錯誤憑證

### TestRealAPIDevices - 裝置操作
- ✅ `test_get_devices` - 取得裝置列表
- ✅ `test_get_device_status` - 取得裝置狀態

### TestRealAPICommands - 控制命令
- ⏭️ `test_send_command` - 發送控制命令（預設跳過）

### TestRealAPITokenManagement - Token 管理
- ✅ `test_token_refresh` - Token 刷新測試

## 🔍 測試輸出範例

有憑證時：
```
integration/test_real_api.py::TestRealAPIDevices::test_get_devices PASSED

✅ 找到 3 個裝置
   第一個裝置: 客廳冷氣 (AC-001)

✅ 裝置狀態: 客廳冷氣
   狀態碼數量: 42
   0x00: 1
   0x01: 0
   0x02: 3
   ...
```

無憑證時：
```
integration/test_real_api.py::TestRealAPILogin::test_login_success SKIPPED
需要設定 PANASONIC_ACCOUNT 和 PANASONIC_PASSWORD 環境變數
```

## 🛡️ 安全建議

1. **不要** commit 包含真實憑證的檔案
2. **建議** 使用測試專用帳號
3. **小心** 控制命令測試（已預設跳過）
4. **定期** 更換測試帳號密碼

## 🐛 故障排除

### 測試全部跳過
```bash
# 檢查環境變數
echo $PANASONIC_ACCOUNT
echo $PANASONIC_PASSWORD

# 確認已設定
export PANASONIC_ACCOUNT='your_account'
export PANASONIC_PASSWORD='your_password'
```

### 登入失敗
- 檢查帳號密碼是否正確
- 確認網路連接正常
- 檢查是否需要 proxy 設定

### Token 錯誤
- API 可能有速率限制
- 等待幾分鐘後重試
- 確認帳號狀態正常
