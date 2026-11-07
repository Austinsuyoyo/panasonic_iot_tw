# 真實 API 整合測試

這個目錄包含需要連接真實 Panasonic IoT API 的測試。

## 運作方式

`pytest-homeassistant` 預設會阻擋所有對外連線：它換掉 `socket.socket`、只允許連到 `127.0.0.1`,並讓 DNS 解析直接失敗。`conftest.py` 用 `trylast` 的 `pytest_runtest_setup` hook,只在這個目錄把三者都還原，所以單元測試仍然離線。

沒有設定 `PANASONIC_ACCOUNT` / `PANASONIC_PASSWORD` 時，所有測試會自動略過。

`tests/test_direct_api.py` 是 pytest 能跑這些測試之前的獨立腳本，不需要 pytest。

## 🧪 執行測試

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

### TestRealAPIFridgeRegisters - 冰箱暫存器
- ✅ `test_dump_fridge_registers` - 印出冰箱所有暫存器現況
- ✅ `test_door_bit_is_readable` - 門狀態位元可讀
- ✅ `test_status_flags_readable` - 狀態旗標可讀

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
