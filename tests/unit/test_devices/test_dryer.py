"""Unit tests for dryer device implementation."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from custom_components.panasonic_iot_tw.devices.dryer import DryerDevice
from custom_components.panasonic_iot_tw.const import (
    DRYER_AVAILABLE_STATUS,
    DRYER_AVAILABLE_CYCLES
)


class TestDryerDevice:
    """Test cases for DryerDevice class."""

    @pytest.fixture
    def mock_coordinator(self):
        """Create a mock coordinator with dryer data."""
        coordinator = Mock()
        coordinator.data = {
            0: {
                "status": {
                    "0x05": 120,  # Drying remaining time: 120 minutes
                    "0x15": 2,    # Schedule remaining time: 2 hours
                    "0x34": 12,   # Engineering info: binary 1100 (drying=8, air_flow=4)
                    "0x50": 2,    # Operation status: 2 (running)
                    "0x55": 1,    # Cycle message: 1
                    "0x64": 6,    # Drying mode params: binary 0110 (air_flow=4, soft_cooling=2)
                    "0x74": 1,    # Remote control allowed: 1
                }
            }
        }
        coordinator.last_update_success = True
        return coordinator

    @pytest.fixture
    def mock_device_data(self):
        """Create mock device data."""
        return {
            "device_id": "dryer_test_001",
            "nickname": "測試烘乾機",
            "model": "Test Dryer Model",
            "version": "1.0.0",
            "available": True,
            "device_type": 5,  # Assuming 5 is dryer type
        }

    @pytest.fixture
    def dryer_device(self, mock_coordinator, mock_device_data):
        """Create a DryerDevice instance for testing."""
        return DryerDevice(mock_coordinator, 0, mock_device_data)

    def test_device_initialization(self, dryer_device, mock_device_data):
        """Test proper device initialization."""
        assert dryer_device.device_key == 0
        assert dryer_device._device_data == mock_device_data
        assert dryer_device.device_id == "dryer_test_001"
        assert dryer_device.model == "Test Dryer Model"

    def test_command_constants(self):
        """Test that all command constants are properly defined."""
        assert DryerDevice.DRYING_REMAINING_TIME_COMMAND == "0x05"
        assert DryerDevice.SCHEDULE_REMAINING_TIME_COMMAND == "0x15"
        assert DryerDevice.ENGINEERING_INFO_COMMAND == "0x34"
        assert DryerDevice.OPERATION_STATUS_COMMAND == "0x50"
        assert DryerDevice.CYCLE_MESSAGE_COMMAND == "0x55"
        assert DryerDevice.REMOTE_CONTROL_COMMAND == "0x74"

    def test_device_data_available_when_operation_status_normal(self, dryer_device):
        """Test device_data returns available=True when operation status is not 0."""
        device_data = dryer_device.device_data
        assert device_data["available"] is True

    def test_device_data_unavailable_when_operation_status_zero(self, mock_coordinator, mock_device_data):
        """Test device_data returns available=False when operation status is 0."""
        # Set operation status to 0 (not displayed)
        mock_coordinator.data[0]["status"]["0x50"] = 0
        dryer_device = DryerDevice(mock_coordinator, 0, mock_device_data)

        device_data = dryer_device.device_data
        assert device_data["available"] is False

    def test_device_data_error_handling(self, mock_coordinator, mock_device_data):
        """Test device_data handles errors gracefully."""
        # Remove status data to cause error
        mock_coordinator.data[0] = {}
        dryer_device = DryerDevice(mock_coordinator, 0, mock_device_data)

        device_data = dryer_device.device_data
        # Should fallback to original availability on error
        assert device_data["available"] is True

    def test_get_sensor_entities_count(self, dryer_device, mock_coordinator):
        """Test that get_sensor_entities returns correct number of sensors."""
        sensors = dryer_device.get_sensor_entities(mock_coordinator)
        assert len(sensors) == 9  # 2 time + 2 status + error code + 4 raw registers

    def test_get_sensor_entities_types(self, dryer_device, mock_coordinator):
        """Test that sensor entities have correct types and properties."""
        with patch('custom_components.panasonic_iot_tw.sensor.PanasonicSensor') as mock_sensor_class:
            mock_sensor_instance = Mock()
            mock_sensor_class.return_value = mock_sensor_instance

            sensors = dryer_device.get_sensor_entities(mock_coordinator)

            # Should create 6 sensors
            assert mock_sensor_class.call_count == 9

            # Check specific sensor configurations
            calls = mock_sensor_class.call_args_list

            # First call - drying remaining time
            args, kwargs = calls[0]
            assert kwargs['command_type'] == "0x05"
            assert kwargs['sensor_key'] == "drying_remaining_time"
            assert kwargs['device_class'] == SensorDeviceClass.DURATION
            assert kwargs['unit'] == UnitOfTime.MINUTES

            # Second call - schedule remaining time
            args, kwargs = calls[1]
            assert kwargs['command_type'] == "0x15"
            assert kwargs['sensor_key'] == "schedule_remaining_time"
            assert kwargs['device_class'] == SensorDeviceClass.DURATION
            assert kwargs['unit'] == UnitOfTime.HOURS

    def test_get_binary_sensor_entities_count(self, dryer_device, mock_coordinator):
        """Test that get_binary_sensor_entities returns correct number of sensors."""
        sensors = dryer_device.get_binary_sensor_entities(mock_coordinator)
        assert len(sensors) == 4  # 3 engineering + 1 remote control

    def test_get_binary_sensor_entities_types(self, dryer_device, mock_coordinator):
        """Test that binary sensor entities have correct configurations."""
        with patch('custom_components.panasonic_iot_tw.binary_sensor.PanasonicBinarySensor') as mock_sensor_class:
            mock_sensor_instance = Mock()
            mock_sensor_class.return_value = mock_sensor_instance

            sensors = dryer_device.get_binary_sensor_entities(mock_coordinator)

            # Should create 4 binary sensors
            assert mock_sensor_class.call_count == 4

            calls = mock_sensor_class.call_args_list

            # Check engineering info sensors (first 3)
            for i in range(3):
                args, kwargs = calls[i]
                assert kwargs['command_type'] == "0x34"  # Engineering info command
                assert kwargs['device_class'] == BinarySensorDeviceClass.RUNNING

            # Check bit masks for engineering info
            assert calls[0][1]['bit_mask'] == 8  # drying
            assert calls[1][1]['bit_mask'] == 4  # air_flow
            assert calls[2][1]['bit_mask'] == 2  # soft_cooling

            # Check remote control sensor (last one)
            args, kwargs = calls[3]
            assert kwargs['command_type'] == "0x74"
            assert kwargs['sensor_key'] == "remote_control_allowed"
            # Panel permission is not connectivity; it is a diagnostic flag
            assert 'device_class' not in kwargs
            assert kwargs['entity_category'] == EntityCategory.DIAGNOSTIC

    def test_empty_entity_methods(self, dryer_device, mock_coordinator):
        """Test that unsupported entity types return empty lists."""
        assert dryer_device.get_switch_entities(mock_coordinator) == []
        assert dryer_device.get_select_entities(mock_coordinator) == []
        assert dryer_device.get_number_entities(mock_coordinator) == []
        assert dryer_device.get_climate_entities(mock_coordinator) == []
        assert dryer_device.get_humidifier_entities(mock_coordinator) == []
        assert dryer_device.get_button_entities(mock_coordinator) == []

    def test_sensor_inheritance_pattern(self, dryer_device, mock_coordinator):
        """Test that sensors properly inherit from base device."""
        # This tests the inherited methods from StatusReader and BaseDevice
        with patch.object(dryer_device, 'get_int_status', return_value=2) as mock_get_int:
            device_data = dryer_device.device_data

            # Should call get_int_status for operation status
            mock_get_int.assert_called_with("0x50", default=1)
            assert device_data["available"] is True

    @pytest.mark.parametrize("operation_status,expected_available", [
        (0, False),   # not displayed - should be unavailable
        (1, True),    # standby - should be available
        (2, True),    # running - should be available
        (3, True),    # reserved - should be available
        (4, True),    # reserved - should be available
        (5, True),    # finished - should be available
        (8, True),    # error - should be available (for diagnostics)
    ])
    def test_device_availability_by_operation_status(self, mock_coordinator, mock_device_data, operation_status, expected_available):
        """Test device availability for all operation status codes."""
        mock_coordinator.data[0]["status"]["0x50"] = operation_status
        dryer_device = DryerDevice(mock_coordinator, 0, mock_device_data)

        device_data = dryer_device.device_data
        assert device_data["available"] == expected_available

    def test_device_data_preserves_original_data(self, dryer_device, mock_device_data):
        """Test that device_data preserves all original data except availability."""
        device_data = dryer_device.device_data

        # Should preserve all original fields
        assert device_data["device_id"] == mock_device_data["device_id"]
        assert device_data["nickname"] == mock_device_data["nickname"]
        assert device_data["model"] == mock_device_data["model"]
        assert device_data["version"] == mock_device_data["version"]
        assert device_data["device_type"] == mock_device_data["device_type"]

        # Should not modify the original data object
        assert dryer_device._device_data is mock_device_data
        assert device_data is not mock_device_data  # Should be a copy

    def test_logging_on_operation_status_zero(self, mock_coordinator, mock_device_data):
        """Test that appropriate logging occurs when operation status is 0."""
        mock_coordinator.data[0]["status"]["0x50"] = 0

        with patch('custom_components.panasonic_iot_tw.devices.dryer._LOGGER') as mock_logger:
            dryer_device = DryerDevice(mock_coordinator, 0, mock_device_data)
            _ = dryer_device.device_data

            # Should log debug message about unavailability
            mock_logger.debug.assert_called_once()
            assert "sensors unavailable" in str(mock_logger.debug.call_args)
            assert "operation status = 0" in str(mock_logger.debug.call_args)

    def test_error_logging_on_exception(self, mock_coordinator, mock_device_data):
        """Test that errors are properly logged when checking operation status fails."""
        # Create a coordinator that will cause an exception
        mock_coordinator.data = None

        with patch('custom_components.panasonic_iot_tw.devices.dryer._LOGGER') as mock_logger:
            dryer_device = DryerDevice(mock_coordinator, 0, mock_device_data)
            device_data = dryer_device.device_data

            # Should log warning about error
            mock_logger.warning.assert_called_once()
            assert "Error checking dryer operation status" in str(mock_logger.warning.call_args)

            # Should fallback to original availability
            assert device_data["available"] is True