#!/usr/bin/env python3
"""
真實 API 測試腳本 - 獨立執行版本

⚠️ 為何需要這個腳本？

由於 pytest-homeassistant-custom-component 強制啟用 socket 阻擋，
無法透過 pytest 執行需要真實網路連線的測試。

這個腳本可以直接執行，不依賴 pytest，避免 socket 限制。

🔮 未來計畫：
   等待 https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/pull/218
   合併後，這些測試將整合進 tests/integration/test_real_api.py，
   屆時可以刪除此檔案。

使用方式：
  python tests/test_direct_api.py

環境變數：
  PANASONIC_ACCOUNT - Panasonic 帳號
  PANASONIC_PASSWORD - Panasonic 密碼

相關文件：
  - tests/integration/README.md - 完整整合計畫說明
  - tests/integration/test_real_api.py - pytest 格式測試（待啟用）
"""
import asyncio
import aiohttp
import os
import sys
from pathlib import Path

# 加入專案路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.panasonic_iot_tw.services.smart_app import SmartApp


class TestResults:
    """測試結果統計"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_pass(self, name):
        self.passed += 1
        self.tests.append((name, "PASSED"))
        print(f"  ✅ {name}")

    def add_fail(self, name, error):
        self.failed += 1
        self.tests.append((name, f"FAILED: {error}"))
        print(f"  ❌ {name}: {error}")

    def summary(self):
        print("\n" + "=" * 60)
        print(f"測試結果: {self.passed} passed, {self.failed} failed")
        if self.failed > 0:
            print("\n失敗的測試:")
            for name, status in self.tests:
                if status.startswith("FAILED"):
                    print(f"  - {name}: {status}")
        print("=" * 60)


async def test_login(smartapp, results):
    """測試 1: 登入功能"""
    try:
        result = await smartapp.login()
        # login() 返回 token 字典或 True
        assert result is not None and result is not False, f"登入失敗，返回值: {result}"
        assert smartapp._token_manager.cp_token is not None, "未取得 Token"
        results.add_pass("test_login")
        token = smartapp._token_manager.cp_token
        print(f"     Token: {token[:20]}...{token[-10:]}")
        return True
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        results.add_fail("test_login", str(e))
        print(f"\n詳細錯誤:\n{error_detail}")
        return False


async def test_get_devices(smartapp, results):
    """測試 2: 取得裝置列表"""
    try:
        devices = await smartapp.get_devices()
        assert isinstance(devices, list), "裝置列表格式錯誤"
        assert len(devices) >= 0, "裝置數量錯誤"
        results.add_pass("test_get_devices")
        print(f"     找到 {len(devices)} 個裝置")
        return devices
    except Exception as e:
        results.add_fail("test_get_devices", str(e))
        return []


async def test_device_info(devices, results):
    """測試 3: 驗證裝置資訊"""
    if len(devices) == 0:
        results.add_pass("test_device_info (skipped - no devices)")
        return

    try:
        device = devices[0]
        assert "device_id" in device, "缺少 device_id"
        assert "nickname" in device, "缺少 nickname"
        assert "model" in device, "缺少 model"
        results.add_pass("test_device_info")
        print(f"     裝置: {device.get('nickname')} ({device.get('model')})")
    except Exception as e:
        results.add_fail("test_device_info", str(e))


async def main():
    """執行所有測試"""
    account = os.getenv("PANASONIC_ACCOUNT")
    password = os.getenv("PANASONIC_PASSWORD")

    if not account or not password:
        print("❌ 錯誤: 請設定環境變數")
        print("   export PANASONIC_ACCOUNT='your_account@example.com'")
        print("   export PANASONIC_PASSWORD='your_password'")
        return False

    print("🧪 Panasonic IoT TW 真實 API 測試")
    print("=" * 60)
    print(f"帳號: {account}")
    print("=" * 60)

    results = TestResults()

    async with aiohttp.ClientSession() as session:
        smartapp = SmartApp(session, account, password)

        print("\n執行測試:")

        # 測試 1: 登入
        if not await test_login(smartapp, results):
            results.summary()
            return False

        # 測試 2: 取得裝置
        devices = await test_get_devices(smartapp, results)

        # 測試 3: 驗證裝置資訊
        await test_device_info(devices, results)

        # 顯示裝置詳細資訊
        if devices:
            print("\n" + "=" * 60)
            print("📱 裝置詳細資訊:")
            print("=" * 60)
            for i, device in enumerate(devices, 1):
                print(f"\n裝置 {i}:")
                print(f"  ID: {device.get('device_id')}")
                print(f"  名稱: {device.get('nickname')}")
                print(f"  型號: {device.get('model')}")
                print(f"  類型: {device.get('device_type')}")

    results.summary()
    return results.failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
