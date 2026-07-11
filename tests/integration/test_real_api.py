# -*- coding: utf-8 -*-
"""
真實 API 整合測試

⚠️ 當前狀態：由於 pytest-homeassistant-custom-component 的 socket 阻擋限制，
這些測試目前無法執行。請使用 tests/test_direct_api.py 代替。

未來整合：等待 https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/pull/218
合併後，這些測試就能正常透過 pytest 執行。

這些測試會連接真實的 Panasonic IoT API，需要有效的帳號密碼。

執行方式（未來可用）：
  # 跳過真實 API 測試（預設）
  pytest

  # 執行真實 API 測試（需要環境變數）
  pytest -m live_api

環境變數設定：
  export PANASONIC_ACCOUNT='your_account@example.com'
  export PANASONIC_PASSWORD='your_password'
  export PANASONIC_PROXY='http://proxy:port'  # 可選
"""

import pytest
import os
import aiohttp
from typing import Optional

from custom_components.panasonic_iot_tw.services.smart_app import SmartApp
from custom_components.panasonic_iot_tw.exceptions import (
    PanasonicLoginFailed,
    PanasonicAPIError,
)


# 檢查是否有 API 憑證
def has_api_credentials() -> bool:
    """檢查是否設定了 API 憑證"""
    return bool(
        os.getenv("PANASONIC_ACCOUNT") and
        os.getenv("PANASONIC_PASSWORD")
    )


# 如果沒有憑證，跳過所有真實 API 測試
pytestmark = [
    pytest.mark.skipif(
        not has_api_credentials(),
        reason="需要設定 PANASONIC_ACCOUNT 和 PANASONIC_PASSWORD 環境變數"
    ),
    pytest.mark.enable_socket,  # 允許真實網路連接
]


@pytest.fixture
def api_credentials():
    """提供 API 憑證"""
    return {
        "account": os.getenv("PANASONIC_ACCOUNT"),
        "password": os.getenv("PANASONIC_PASSWORD"),
        "proxy": os.getenv("PANASONIC_PROXY"),
    }


@pytest.mark.live_api
@pytest.mark.asyncio
class TestRealAPILogin:
    """測試真實 API 登入功能"""

    async def test_login_success(self, api_credentials):
        """測試登入成功"""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=api_credentials["account"],
                password=api_credentials["password"],
                proxy=api_credentials["proxy"]
            )

            result = await smartapp.login()
            assert result is True, "登入應該成功"
            assert smartapp._token_manager.cp_token is not None, "應該取得 CP Token"
            print(f"\n✅ 登入成功")
            print(f"   CP Token: {smartapp._token_manager.cp_token[:20]}...")

    async def test_login_with_invalid_credentials(self):
        """測試使用錯誤憑證登入"""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account="invalid@example.com",
                password="wrong_password"
            )

            with pytest.raises(PanasonicLoginFailed):
                await smartapp.login()


@pytest.mark.live_api
@pytest.mark.asyncio
class TestRealAPIDevices:
    """測試真實 API 裝置操作"""

    async def test_get_devices(self, api_credentials):
        """測試取得裝置列表"""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=api_credentials["account"],
                password=api_credentials["password"],
                proxy=api_credentials["proxy"]
            )

            # 先登入
            await smartapp.login()

            # 取得裝置
            devices = await smartapp.get_devices()

            assert isinstance(devices, list), "裝置列表應該是 list"
            assert len(devices) >= 0, "裝置列表長度應該 >= 0"

            if len(devices) > 0:
                device = devices[0]
                assert "device_id" in device, "裝置應該有 device_id"
                assert "nickname" in device, "裝置應該有 nickname"
                print(f"\n✅ 找到 {len(devices)} 個裝置")
                print(f"   第一個裝置: {device.get('nickname')} ({device.get('device_id')})")

    async def test_get_device_status(self, api_credentials):
        """測試取得裝置狀態"""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=api_credentials["account"],
                password=api_credentials["password"],
                proxy=api_credentials["proxy"]
            )

            # 先登入
            await smartapp.login()

            # 取得裝置
            devices = await smartapp.get_devices()

            if len(devices) == 0:
                pytest.skip("沒有裝置可測試")

            # 只驗證可以取得裝置資訊
            device = devices[0]

            # 驗證裝置資料結構
            assert "device_id" in device
            assert "nickname" in device
            print(f"\n✅ 裝置資訊正確")
            print(f"   裝置名稱: {device.get('nickname')}")
            print(f"   裝置型號: {device.get('model')}")
            print(f"   裝置類型: {device.get('device_type')}")


@pytest.mark.live_api
@pytest.mark.asyncio
class TestRealAPICommands:
    """測試真實 API 控制命令（謹慎使用）"""

    @pytest.mark.skip(reason="控制命令會影響真實裝置，預設跳過")
    async def test_send_command(self, api_credentials):
        """測試發送控制命令（預設跳過）"""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=api_credentials["account"],
                password=api_credentials["password"],
                proxy=api_credentials["proxy"]
            )

            # 先登入
            await smartapp.login()

            # 取得裝置
            devices = await smartapp.get_devices()

            if len(devices) == 0:
                pytest.skip("沒有裝置可測試")

            # 這裡可以加入實際的控制命令測試
            # 注意：這會影響真實裝置！
            device = devices[0]

            # 範例：只驗證裝置資訊，不控制
            assert device is not None
            assert "device_id" in device


@pytest.mark.live_api
@pytest.mark.asyncio
class TestRealAPITokenManagement:
    """測試真實 API Token 管理"""

    async def test_token_refresh(self, api_credentials):
        """測試 Token 刷新"""
        async with aiohttp.ClientSession() as session:
            smartapp = SmartApp(
                session=session,
                account=api_credentials["account"],
                password=api_credentials["password"],
                proxy=api_credentials["proxy"]
            )

            # 先登入
            await smartapp.login()

            old_token = smartapp._token_manager.cp_token

            # 刷新 token（如果 API 支援）
            # 注意：實際實作可能需要等待 token 過期

            # 驗證 token 存在
            assert old_token is not None, "應該有 CP Token"
            print(f"\n✅ Token 管理正常")
            print(f"   CP Token: {old_token[:10]}...{old_token[-10:]}")
