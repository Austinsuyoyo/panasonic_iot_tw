"""Unexpected HTTP errors must fail loudly, not turn into empty successes."""
import json
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.panasonic_iot_tw.exceptions import (
    PanasonicAPIError,
    PanasonicLoginFailed,
)
from custom_components.panasonic_iot_tw.services.api_client import ApiClient
from custom_components.panasonic_iot_tw.services.device_service import DeviceService
from custom_components.panasonic_iot_tw.services.token_manager import TokenManager


class _FakeResponse:
    status = 500

    async def text(self):
        return "Internal Server Error"


class _FakeSession:
    async def request(self, *args, **kwargs):
        return _FakeResponse()


async def test_unexpected_http_status_raises():
    """A 5xx no longer comes back as an empty dict."""
    client = ApiClient(_FakeSession())
    with pytest.raises(PanasonicAPIError):
        await client.request("GET", "https://example.invalid/api", apply_delay=False)


async def test_send_command_reports_failure_on_http_error():
    """A failed DeviceSetCommand must not be reported as a success."""
    client = ApiClient(_FakeSession())
    token_manager = Mock()
    token_manager.ensure_authenticated = AsyncMock()
    token_manager.get_device_auth_headers.return_value = {}
    service = DeviceService(client, token_manager)

    device = {"Auth": "auth", "GWID": "gwid", "NickName": "Test Device"}
    assert await service.send_command(device, "0x00", 1) is False


class _Fake417:
    status = 417

    def __init__(self, body):
        self._body = body

    async def json(self):
        return json.loads(self._body)

    async def text(self):
        return self._body


class _Fake417Session:
    def __init__(self, body):
        self._body = body

    async def request(self, *args, **kwargs):
        return _Fake417(self._body)


# Verbatim from the cloud on 2026-10-04 (one as JSON StateMsg, one as plain text).
_SQL_DOWN = '{"StateMsg": "建立連接至 SQL Server 時，發生網路相關或執行個體特定的錯誤。找不到或無法存取伺服器。"}'
_SQL_TIMEOUT = "已超過連接逾時的設定。在嘗試使用登入前的信號交換確認時超過逾時等待的時間。"


@pytest.mark.parametrize("body", [_SQL_DOWN, _SQL_TIMEOUT])
async def test_cloud_database_failure_is_not_an_auth_error(body):
    """A cloud SQL outage must not count towards reauth."""
    client = ApiClient(_Fake417Session(body))
    with pytest.raises(PanasonicAPIError):
        await client.request("GET", "https://example.invalid/api", apply_delay=False)


async def test_unknown_417_text_still_reports_login_failure():
    """Unparseable 417s other than DB failures (e.g. a bad CPToken) keep their meaning."""
    client = ApiClient(_Fake417Session("Invalid CPToken"))
    with pytest.raises(PanasonicLoginFailed):
        await client.request("GET", "https://example.invalid/api", apply_delay=False)


async def test_login_does_not_relabel_server_failure_as_login_failure():
    """A server-side error during login must reach the coordinator unchanged."""
    api_client = Mock(spec=ApiClient)
    api_client.request = AsyncMock(side_effect=PanasonicAPIError("backend down"))
    manager = TokenManager(api_client, "account@example.com", "password")
    with pytest.raises(PanasonicAPIError):
        await manager.login()
