"""Unit tests for token/credential security in TokenManager and ApiClient."""
import asyncio
from datetime import datetime, timedelta

import pytest
from unittest.mock import AsyncMock, Mock

from custom_components.panasonic_iot_tw.services.api_client import (
    ApiClient,
    _sanitize_data,
    _sanitize_text,
)
from custom_components.panasonic_iot_tw.services.token_manager import TokenManager


def _make_expired_manager(request_mock):
    """Build a TokenManager with a valid-but-expired token and a mocked ApiClient."""
    api_client = Mock(spec=ApiClient)
    api_client.request = request_mock
    manager = TokenManager(api_client, "account@example.com", "password")
    manager._refresh_token = "old_refresh_token"
    manager._cp_token = "old_cp_token"
    manager._token_expires_at = datetime.now() - timedelta(seconds=1)
    return manager, api_client


class TestRefreshTokenLogging:
    """The refresh request must never be logged with its sensitive body."""

    @pytest.mark.asyncio
    async def test_refresh_token_request_uses_log_false(self):
        request_mock = AsyncMock(
            return_value={"RefreshToken": "new_refresh_token", "CPToken": "new_cp_token"}
        )
        manager, api_client = _make_expired_manager(request_mock)

        await manager.refresh_token()

        api_client.request.assert_awaited_once()
        assert api_client.request.await_args.kwargs.get("log") is False


class TestConcurrentRefresh:
    """Overlapping refreshes must collapse to a single underlying API call."""

    @pytest.mark.asyncio
    async def test_concurrent_refresh_triggers_single_api_call(self):
        call_count = 0

        async def fake_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Hold the lock long enough for the other coroutines to queue up.
            await asyncio.sleep(0.01)
            return {"RefreshToken": "new_refresh_token", "CPToken": "new_cp_token"}

        manager, _ = _make_expired_manager(AsyncMock(side_effect=fake_request))

        await asyncio.gather(*[manager.refresh_token() for _ in range(5)])

        assert call_count == 1


class TestPayloadSanitization:
    """Defense in depth: sensitive keys are masked even when log=True."""

    def test_sanitize_data_masks_sensitive_keys(self):
        data = {
            "RefreshToken": "11111111-2222-4333-8444",
            "MemId": "account@example.com",
            "PW": "super-secret",
            "AppToken": "AAAAAAAA-BBBB-4CCC",
            "Model": "CS-K25YA2",
        }

        sanitized = _sanitize_data(data)
        rendered = str(sanitized)

        assert "11111111-2222-4333-8444" not in rendered
        assert "super-secret" not in rendered
        assert "account@example.com" not in rendered
        assert sanitized["RefreshToken"].endswith("****")
        # Non-sensitive fields stay intact so logs remain useful.
        assert sanitized["Model"] == "CS-K25YA2"

    def test_sanitize_text_masks_response_tokens(self):
        text = '{"CPToken":"ABCDEF123456","RefreshToken":"ZZZZ111122","StateMsg":"Success"}'

        masked = _sanitize_text(text)

        assert "ABCDEF123456" not in masked
        assert "ZZZZ111122" not in masked
        assert "Success" in masked

    def test_sanitize_text_falls_back_for_non_json(self):
        text = 'garbage "CPToken":"ABCDEF123456" trailing'

        masked = _sanitize_text(text)

        assert "ABCDEF123456" not in masked
        assert "trailing" in masked
