"""Unexpected HTTP errors must fail loudly, not turn into empty successes."""
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.panasonic_iot_tw.exceptions import PanasonicAPIError
from custom_components.panasonic_iot_tw.services.api_client import ApiClient
from custom_components.panasonic_iot_tw.services.device_service import DeviceService


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
