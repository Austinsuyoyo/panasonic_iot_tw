"""Unit tests for error handler implementation."""
import pytest
from unittest.mock import Mock, patch
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.panasonic_iot_tw.base.error_handler import ErrorHandler
from custom_components.panasonic_iot_tw.exceptions import (
    PanasonicDeviceOffline,
    PanasonicExceedRateLimit,
    PanasonicTokenExpired,
    PanasonicLoginFailed,
    PanasonicBaseException,
    PanasonicAPIError,
    PanasonicAuthError,
)


class TestErrorHandlerApiError:
    """Test cases for ErrorHandler.handle_api_error method."""

    def test_handle_device_offline_error(self):
        """Test handling of device offline error."""
        error = PanasonicDeviceOffline("Device is offline")
        context = "device_status_update"
        device_name = "Test Device"

        result = ErrorHandler.handle_api_error(error, context, device_name)

        assert result["status"] == "offline"
        assert result["data"] == {}
        assert "should_retry" not in result  # offline doesn't need retry flag

    def test_handle_rate_limit_error(self):
        """Test handling of rate limit exceeded error."""
        error = PanasonicExceedRateLimit("Too many requests")
        context = "api_call"

        result = ErrorHandler.handle_api_error(error, context)

        assert result["status"] == "rate_limited"
        assert result["data"] == {}
        assert result["should_retry"] is True

    def test_handle_token_expired_error(self):
        """Test handling of token expired error."""
        error = PanasonicTokenExpired("Access token expired")
        context = "device_control"
        device_name = "AC Unit"

        result = ErrorHandler.handle_api_error(error, context, device_name)

        assert result["status"] == "token_expired"
        assert result["data"] == {}
        assert result["should_retry"] is True

    def test_handle_login_failed_error(self):
        """Test handling of login failed error."""
        error = PanasonicLoginFailed("Invalid credentials")
        context = "authentication"

        result = ErrorHandler.handle_api_error(error, context)

        assert result["status"] == "login_failed"
        assert result["data"] == {}
        assert result["should_retry"] is False

    def test_handle_generic_panasonic_error(self):
        """Test handling of generic Panasonic API error."""
        error = PanasonicBaseException("Generic API error")
        context = "api_operation"

        result = ErrorHandler.handle_api_error(error, context)

        assert result["status"] == "api_error"
        assert result["data"] == {}
        assert result["should_retry"] is True

    def test_handle_unknown_error(self):
        """Test handling of unknown/unexpected error."""
        error = ValueError("Unknown error type")
        context = "unknown_operation"

        result = ErrorHandler.handle_api_error(error, context)

        assert result["status"] == "unknown_error"
        assert result["data"] == {}
        assert result["should_retry"] is False

    def test_handle_api_error_without_device_name(self):
        """Test error handling without device name."""
        error = PanasonicDeviceOffline("Device offline")
        context = "general_operation"

        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            result = ErrorHandler.handle_api_error(error, context)

            assert result["status"] == "offline"
            mock_logger.debug.assert_called_once()
            # Should not include device name in log message
            call_args = mock_logger.debug.call_args.args
            assert "is offline in %s" in call_args[0]
            assert "general_operation" in call_args
            assert "" in call_args  # device_info empty when no device name

    def test_handle_api_error_with_device_name(self):
        """Test error handling with device name."""
        error = PanasonicExceedRateLimit("Rate limit")
        context = "device_update"
        device_name = "Living Room AC"

        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            result = ErrorHandler.handle_api_error(error, context, device_name)

            assert result["status"] == "rate_limited"
            mock_logger.error.assert_called_once()
            # Should include device name in log message
            log_message = str(mock_logger.error.call_args)
            assert "for device 'Living Room AC'" in log_message

    @pytest.mark.parametrize("error_class,expected_status,expected_retry", [
        (PanasonicDeviceOffline, "offline", None),
        (PanasonicExceedRateLimit, "rate_limited", True),
        (PanasonicTokenExpired, "token_expired", True),
        (PanasonicLoginFailed, "login_failed", False),
        (PanasonicAPIError, "api_error", True),
        (PanasonicAuthError, "api_error", True),
        (Exception, "unknown_error", False),
    ])
    def test_error_handling_matrix(self, error_class, expected_status, expected_retry):
        """Test error handling for all error types."""
        error = error_class("Test error message")
        result = ErrorHandler.handle_api_error(error, "test_context")

        assert result["status"] == expected_status
        assert result["data"] == {}
        if expected_retry is not None:
            assert result["should_retry"] == expected_retry


class TestErrorHandlerCoordinatorError:
    """Test cases for ErrorHandler.handle_coordinator_error method."""

    def test_handle_coordinator_rate_limit_error(self):
        """Test coordinator handling of rate limit error."""
        error = PanasonicExceedRateLimit("Rate limit exceeded")
        context = "coordinator_update"

        with pytest.raises(UpdateFailed) as exc_info:
            ErrorHandler.handle_coordinator_error(error, context)

        assert "Temporary failure in coordinator_update" in str(exc_info.value)

    def test_handle_coordinator_token_expired_error(self):
        """Test coordinator handling of token expired error."""
        error = PanasonicTokenExpired("Token expired")
        context = "data_fetch"

        with pytest.raises(UpdateFailed) as exc_info:
            ErrorHandler.handle_coordinator_error(error, context)

        assert "Temporary failure in data_fetch" in str(exc_info.value)

    def test_handle_coordinator_device_offline_error(self):
        """Test coordinator handling of device offline error."""
        error = PanasonicDeviceOffline("Device offline")
        context = "status_update"

        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            # Should not raise exception for offline devices
            ErrorHandler.handle_coordinator_error(error, context)

            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args.args
            assert "is offline in %s" in call_args[0]
            assert "status_update" in call_args

    def test_handle_coordinator_login_failed_error(self):
        """Test coordinator handling of login failed error."""
        error = PanasonicLoginFailed("Login failed")
        context = "authentication"

        with pytest.raises(UpdateFailed) as exc_info:
            ErrorHandler.handle_coordinator_error(error, context)

        assert "Failed in authentication" in str(exc_info.value)

    def test_handle_coordinator_unknown_error(self):
        """Test coordinator handling of unknown error."""
        error = ValueError("Unknown error")
        context = "unknown_operation"

        with pytest.raises(UpdateFailed) as exc_info:
            ErrorHandler.handle_coordinator_error(error, context)

        assert "Failed in unknown_operation" in str(exc_info.value)


class TestErrorHandlerSafeExecute:
    """Test cases for ErrorHandler.safe_execute method."""

    def test_safe_execute_success(self):
        """Test successful execution of function."""
        def successful_function():
            return "success_result"

        result = ErrorHandler.safe_execute(successful_function, "default", "test_context")
        assert result == "success_result"

    def test_safe_execute_with_exception(self):
        """Test safe execution when function raises exception."""
        def failing_function():
            raise ValueError("Function failed")

        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            result = ErrorHandler.safe_execute(failing_function, "default_value", "test_context")

            assert result == "default_value"
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args.args
            assert "Safe execution failed in %s" in call_args[0]
            assert "test_context" in call_args

    def test_safe_execute_with_none_default(self):
        """Test safe execution with None as default value."""
        def failing_function():
            raise RuntimeError("Runtime error")

        result = ErrorHandler.safe_execute(failing_function, None, "test_context")
        assert result is None

    def test_safe_execute_without_default(self):
        """Test safe execution without providing default value."""
        def failing_function():
            raise Exception("Error")

        result = ErrorHandler.safe_execute(failing_function, context="test_context")
        assert result is None

    def test_safe_execute_lambda_function(self):
        """Test safe execution with lambda function."""
        # Successful lambda
        result = ErrorHandler.safe_execute(lambda: 42, "default", "lambda_test")
        assert result == 42

        # Failing lambda
        result = ErrorHandler.safe_execute(lambda: 1/0, "default", "lambda_test")
        assert result == "default"


class TestErrorHandlerValidateResponse:
    """Test cases for ErrorHandler.validate_response method."""

    def test_validate_response_success(self):
        """Test successful response validation."""
        response = {
            "status": "success",
            "data": {"device_id": "123"},
            "timestamp": "2023-01-01T00:00:00Z"
        }
        required_keys = ["status", "data"]

        result = ErrorHandler.validate_response(response, required_keys, "api_response")
        assert result is True

    def test_validate_response_missing_keys(self):
        """Test response validation with missing required keys."""
        response = {
            "status": "success"
            # Missing "data" key
        }
        required_keys = ["status", "data"]

        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            result = ErrorHandler.validate_response(response, required_keys, "api_response")

            assert result is False
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args.args
            assert "Missing required keys in %s: %s" in call_args[0]
            assert "api_response" in call_args
            assert ["data"] in call_args

    def test_validate_response_invalid_format(self):
        """Test response validation with invalid format (not dict)."""
        response = "invalid_response_string"
        required_keys = ["status"]

        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            result = ErrorHandler.validate_response(response, required_keys, "api_response")

            assert result is False
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args.args
            assert "Invalid response format in %s: not a dictionary" in call_args[0]
            assert "api_response" in call_args

    def test_validate_response_empty_required_keys(self):
        """Test response validation with empty required keys list."""
        response = {"any": "data"}
        required_keys = []

        result = ErrorHandler.validate_response(response, required_keys, "test_context")
        assert result is True

    def test_validate_response_none_response(self):
        """Test response validation with None response."""
        response = None
        required_keys = ["status"]

        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            result = ErrorHandler.validate_response(response, required_keys, "test_context")

            assert result is False
            mock_logger.error.assert_called_once()


class TestErrorHandlerLogDeviceStatus:
    """Test cases for ErrorHandler.log_device_status method."""

    def test_log_device_status_error_status(self):
        """Test logging error status."""
        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            ErrorHandler.log_device_status("Test Device", "error", "Connection failed")

            mock_logger.warning.assert_called_once()
            log_message = str(mock_logger.warning.call_args)
            assert "Device 'Test Device' status: error - Connection failed" in log_message

    def test_log_device_status_success_status(self):
        """Test logging success status."""
        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            ErrorHandler.log_device_status("Test Device", "success", "Updated successfully")

            mock_logger.debug.assert_called_once()
            log_message = str(mock_logger.debug.call_args)
            assert "Device 'Test Device' status: success - Updated successfully" in log_message

    def test_log_device_status_info_status(self):
        """Test logging info status."""
        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            ErrorHandler.log_device_status("Test Device", "connecting", "Attempting connection")

            mock_logger.info.assert_called_once()
            log_message = str(mock_logger.info.call_args)
            assert "Device 'Test Device' status: connecting - Attempting connection" in log_message

    def test_log_device_status_without_details(self):
        """Test logging status without details."""
        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            ErrorHandler.log_device_status("Test Device", "online")

            mock_logger.debug.assert_called_once()
            log_message = str(mock_logger.debug.call_args)
            assert "Device 'Test Device' status: online" in log_message
            assert " - " not in log_message  # No details separator

    @pytest.mark.parametrize("status,expected_log_level", [
        ("offline", "warning"),
        ("error", "warning"),
        ("failed", "warning"),
        ("online", "debug"),
        ("success", "debug"),
        ("updated", "debug"),
        ("connecting", "info"),
        ("unknown", "info"),
    ])
    def test_log_device_status_levels(self, status, expected_log_level):
        """Test that different statuses use correct log levels."""
        with patch('custom_components.panasonic_iot_tw.base.error_handler._LOGGER') as mock_logger:
            ErrorHandler.log_device_status("Test Device", status)

            # Get the expected logger method
            expected_method = getattr(mock_logger, expected_log_level)
            expected_method.assert_called_once()


class TestErrorHandlerIntegration:
    """Integration tests for ErrorHandler combining multiple methods."""

    def test_api_error_to_coordinator_error_flow(self):
        """Test the flow from API error to coordinator error handling."""
        original_error = PanasonicExceedRateLimit("API rate limit exceeded")
        context = "device_update"

        # First handle as API error
        api_result = ErrorHandler.handle_api_error(original_error, context, "Test Device")
        assert api_result["status"] == "rate_limited"
        assert api_result["should_retry"] is True

        # Then handle as coordinator error (should raise UpdateFailed)
        with pytest.raises(UpdateFailed) as exc_info:
            ErrorHandler.handle_coordinator_error(original_error, context)

        assert "Temporary failure" in str(exc_info.value)

    def test_safe_execute_with_error_handler_integration(self):
        """Test safe_execute integrating with error handling patterns."""
        def api_function():
            raise PanasonicTokenExpired("Token expired during operation")

        # Use safe_execute to handle the API call
        result = ErrorHandler.safe_execute(api_function, {}, "api_call")

        # Should return default value when function fails
        assert result == {}

        # Can also use safe_execute with error handling
        def error_handling_function():
            try:
                return api_function()
            except Exception as e:
                return ErrorHandler.handle_api_error(e, "safe_api_call")

        result = ErrorHandler.safe_execute(error_handling_function, None, "safe_api_call")
        assert result["status"] == "token_expired"

    def test_response_validation_with_error_logging(self):
        """Test response validation combined with device status logging."""
        invalid_response = {"status": "error"}  # Missing required data
        required_keys = ["status", "data", "timestamp"]
        device_name = "Test Device"

        # Validate response
        is_valid = ErrorHandler.validate_response(invalid_response, required_keys, "api_response")
        assert is_valid is False

        # Log device status based on validation result
        if not is_valid:
            ErrorHandler.log_device_status(device_name, "error", "Invalid response format")

        # Both should have logged appropriately
        # (Testing the integration pattern, actual logging tested in individual tests)