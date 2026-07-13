"""Unit tests for ReportService nightly-maintenance scheduling and failure backoff.

The report API is unreliable between local midnight and 08:00 (backend day is
8h ahead of Taipei). These tests pin the scheduling / backoff / empty-result
behaviour by freezing ``datetime`` inside the report_service module namespace.
"""
from datetime import datetime, timedelta

import pytest
from unittest.mock import AsyncMock, Mock, patch

from custom_components.panasonic_iot_tw.services import report_service
from custom_components.panasonic_iot_tw.services.report_service import (
    FAILURE_RETRY_SECONDS,
    NIGHTLY_MAINTENANCE_END_HOUR,
    ReportService,
)

# A refrigerator is the only device type that supports the report sensors.
DEVICE_LIST = [{"device_type": 2, "gwid": "GW1"}]

# A successful report payload: one supported device present in GwList.
SUCCESS_RESPONSE = {"GwList": [{"GwID": "GW1", "value": 42}]}

# A syntactically valid but empty payload (nightly-maintenance symptom).
EMPTY_RESPONSE = {"GwList": []}


def _make_service():
    """Build a ReportService with mocked collaborators and a mocked request."""
    service = ReportService(api_client=Mock(), token_manager=Mock())
    service._make_report_request = AsyncMock()
    return service


def _freeze(now: datetime):
    """Patch datetime.now() inside the report_service module to ``now``."""
    mock_dt = patch.object(report_service, "datetime").start()
    mock_dt.now.return_value = now
    return mock_dt


@pytest.fixture(autouse=True)
def _stop_patches():
    yield
    patch.stopall()


class TestNightlyMaintenanceWindow:
    """The daily refresh must wait out the 00:00-08:00 maintenance window."""

    @pytest.mark.asyncio
    async def test_date_changed_at_hour_2_serves_cache_without_fetch(self):
        service = _make_service()
        yesterday = datetime(2026, 7, 10, 23, 0, 0)
        service._last_energy_fetch = yesterday
        service._energy_cache = {"GW1": {"value": 1}}
        _freeze(datetime(2026, 7, 11, 2, 0, 0))

        result = await service.get_energy_data(DEVICE_LIST)

        service._make_report_request.assert_not_awaited()
        assert result == {"GW1": {"value": 1}}
        assert service._last_energy_fetch == yesterday

    @pytest.mark.asyncio
    @pytest.mark.parametrize("hour", [NIGHTLY_MAINTENANCE_END_HOUR, 9])
    async def test_date_changed_after_window_fetches(self, hour):
        service = _make_service()
        service._last_energy_fetch = datetime(2026, 7, 10, 23, 0, 0)
        service._energy_cache = {"GW1": {"value": 1}}
        service._make_report_request.return_value = SUCCESS_RESPONSE
        now = datetime(2026, 7, 11, hour, 0, 0)
        _freeze(now)

        result = await service.get_energy_data(DEVICE_LIST)

        service._make_report_request.assert_awaited_once()
        assert result == {"GW1": {"GwID": "GW1", "value": 42}}
        assert service._last_energy_fetch == now

    @pytest.mark.asyncio
    async def test_never_fetched_at_hour_2_attempts_fetch(self):
        service = _make_service()
        service._make_report_request.return_value = SUCCESS_RESPONSE
        _freeze(datetime(2026, 7, 11, 2, 0, 0))

        result = await service.get_energy_data(DEVICE_LIST)

        service._make_report_request.assert_awaited_once()
        assert result == {"GW1": {"GwID": "GW1", "value": 42}}


class TestFailureBackoff:
    """A failing fetch must back off for FAILURE_RETRY_SECONDS."""

    @pytest.mark.asyncio
    async def test_failed_fetch_backs_off_then_retries(self):
        service = _make_service()
        service._last_energy_fetch = datetime(2026, 7, 10, 23, 0, 0)
        service._energy_cache = {"GW1": {"value": 1}}
        service._make_report_request.return_value = None

        # First call at hour 9: fetch attempted, fails, records failure.
        mock_dt = _freeze(datetime(2026, 7, 11, 9, 0, 0))
        result = await service.get_energy_data(DEVICE_LIST)
        assert service._make_report_request.await_count == 1
        assert result == {"GW1": {"value": 1}}
        assert service._last_failed_fetch is not None
        assert service._last_energy_fetch == datetime(2026, 7, 10, 23, 0, 0)

        # Second call 10 min later: still inside backoff window, no API call.
        mock_dt.now.return_value = datetime(2026, 7, 11, 9, 10, 0)
        await service.get_energy_data(DEVICE_LIST)
        assert service._make_report_request.await_count == 1

        # After backoff expires: retried.
        mock_dt.now.return_value = datetime(2026, 7, 11, 9, 0, 0) + timedelta(
            seconds=FAILURE_RETRY_SECONDS + 60
        )
        await service.get_energy_data(DEVICE_LIST)
        assert service._make_report_request.await_count == 2


class TestEmptyResultGuard:
    """An empty payload while a good cache exists is treated as failure."""

    @pytest.mark.asyncio
    async def test_empty_response_preserves_cache_and_flags_failure(self):
        service = _make_service()
        last_fetch = datetime(2026, 7, 10, 23, 0, 0)
        service._last_energy_fetch = last_fetch
        service._energy_cache = {"GW1": {"value": 1}}
        service._make_report_request.return_value = EMPTY_RESPONSE
        _freeze(datetime(2026, 7, 11, 9, 0, 0))

        result = await service.get_energy_data(DEVICE_LIST)

        service._make_report_request.assert_awaited_once()
        assert result == {"GW1": {"value": 1}}
        assert service._energy_cache == {"GW1": {"value": 1}}
        assert service._last_energy_fetch == last_fetch
        assert service._last_failed_fetch is not None


class TestSuccessClearsBackoff:
    """A successful fetch clears the shared failure timestamp."""

    @pytest.mark.asyncio
    async def test_success_clears_failure_backoff(self):
        service = _make_service()
        # Failure long enough ago that the backoff has expired; the retry
        # succeeds and must clear the failure timestamp.
        service._last_energy_fetch = None
        service._last_failed_fetch = datetime(2026, 7, 11, 8, 20, 0)
        service._make_report_request.return_value = SUCCESS_RESPONSE
        now = datetime(2026, 7, 11, 9, 0, 0)
        _freeze(now)

        result = await service.get_energy_data(DEVICE_LIST)

        service._make_report_request.assert_awaited_once()
        assert result == {"GW1": {"GwID": "GW1", "value": 42}}
        assert service._last_failed_fetch is None
        assert service._last_energy_fetch == now

    @pytest.mark.asyncio
    async def test_startup_respects_failure_backoff(self):
        service = _make_service()
        # Never-fetched (startup) path with a RECENT failure: backoff wins,
        # no API call. Only force_refresh_special_data clears the backoff.
        service._last_energy_fetch = None
        service._last_failed_fetch = datetime(2026, 7, 11, 8, 55, 0)
        _freeze(datetime(2026, 7, 11, 9, 0, 0))

        result = await service.get_energy_data(DEVICE_LIST)

        service._make_report_request.assert_not_awaited()
        assert result == {}
