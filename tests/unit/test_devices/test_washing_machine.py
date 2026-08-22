"""Unit tests for washing machine device implementation."""
import pytest
from unittest.mock import Mock, patch
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory

from custom_components.panasonic_iot_tw.devices.washing_machine import WashingMachineDevice
from custom_components.panasonic_iot_tw.const import (
    WASHING_MACHINE_AVAILABLE_STATUS,
    WASHING_MACHINE_AVAILABLE_CYCLES
)


class TestWashingMachineDevice:
    """Test cases for WashingMachineDevice class."""

    @pytest.fixture
    def mock_coordinator(self):
        """Create a mock coordinator with washing machine data."""
        coordinator = Mock()
        coordinator.data = {
            0: {
                "status": {
                    "0x13": 45,   # Washing remaining time: 45 minutes
                    "0x15": 3,    # Schedule remaining time: 3 hours
                    "0x34": 208,  # Engineering info: binary 11010000 (pre_wash=128, washing=64, rinse=16)
                    "0x50": 2,    # Operation status: 2 (running)
                    "0x55": 1,    # Cycle message: 1
                    "0x64": 1088, # Engineering info ext: binary 10001000000 (pre_wash_ext=1024, washing_ext=64)
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
            "device_id": "washing_machine_test_001",
            "nickname": "測試洗衣機",
            "model": "Test Washing Machine Model",
            "version": "1.0.0",
            "available": True,
            "device_type": 4,  # Assuming 4 is washing machine type
        }

    @pytest.fixture
    def washing_machine_device(self, mock_coordinator, mock_device_data):
        """Create a WashingMachineDevice instance for testing."""
        return WashingMachineDevice(mock_coordinator, 0, mock_device_data)

    def test_device_initialization(self, washing_machine_device, mock_device_data):
        """Test proper device initialization."""
        assert washing_machine_device.device_key == 0
        assert washing_machine_device._device_data == mock_device_data
        assert washing_machine_device.device_id == "washing_machine_test_001"
        assert washing_machine_device.model == "Test Washing Machine Model"

    def test_command_constants(self):
        """Test that all command constants are properly defined."""
        assert WashingMachineDevice.WASHING_REMAINING_TIME_COMMAND == "0x13"
        assert WashingMachineDevice.SCHEDULE_REMAINING_TIME_COMMAND == "0x15"
        assert WashingMachineDevice.ENGINEERING_INFO_COMMAND == "0x34"
        assert WashingMachineDevice.OPERATION_STATUS_COMMAND == "0x50"
        assert WashingMachineDevice.CYCLE_MESSAGE_COMMAND == "0x55"
        assert WashingMachineDevice.REMOTE_CONTROL_COMMAND == "0x74"

    def test_get_sensor_entities_count(self, washing_machine_device, mock_coordinator):
        """Test that get_sensor_entities returns correct number of sensors."""
        sensors = washing_machine_device.get_sensor_entities(mock_coordinator)
        assert len(sensors) == 5  # 2 time + 2 status + error code

    def test_get_sensor_entities_types(self, washing_machine_device, mock_coordinator):
        """Test that sensor entities have correct types and properties."""
        with patch('custom_components.panasonic_iot_tw.sensor.PanasonicSensor') as mock_sensor_class:
            mock_sensor_instance = Mock()
            mock_sensor_class.return_value = mock_sensor_instance

            sensors = washing_machine_device.get_sensor_entities(mock_coordinator)

            # Should create 6 sensors
            assert mock_sensor_class.call_count == 5

            # Check specific sensor configurations
            calls = mock_sensor_class.call_args_list

            # First call - washing remaining time
            args, kwargs = calls[0]
            assert kwargs['command_type'] == "0x13"
            assert kwargs['sensor_key'] == "washing_remaining_time"
            assert kwargs['device_class'] == SensorDeviceClass.DURATION
            assert kwargs['unit'] == UnitOfTime.MINUTES

            # Second call - schedule remaining time
            args, kwargs = calls[1]
            assert kwargs['command_type'] == "0x15"
            assert kwargs['sensor_key'] == "schedule_remaining_time"
            assert kwargs['device_class'] == SensorDeviceClass.DURATION
            assert kwargs['unit'] == UnitOfTime.HOURS

            # Third call - operation status
            args, kwargs = calls[2]
            assert kwargs['command_type'] == "0x50"
            assert kwargs['sensor_key'] == "operation_status"

            # Fourth call - cycle message
            args, kwargs = calls[3]
            assert kwargs['command_type'] == "0x55"
            assert kwargs['sensor_key'] == "cycle_message"

    def test_get_binary_sensor_entities_count(self, washing_machine_device, mock_coordinator):
        """Test that get_binary_sensor_entities returns correct number of sensors."""
        sensors = washing_machine_device.get_binary_sensor_entities(mock_coordinator)
        assert len(sensors) == 6  # 4 engineering + detergent + remote control

    def test_get_binary_sensor_entities_types(self, washing_machine_device, mock_coordinator):
        """Test that binary sensor entities have correct configurations."""
        with patch('custom_components.panasonic_iot_tw.binary_sensor.PanasonicBinarySensor') as mock_sensor_class:
            mock_sensor_instance = Mock()
            mock_sensor_class.return_value = mock_sensor_instance

            sensors = washing_machine_device.get_binary_sensor_entities(mock_coordinator)

            # Should create 5 binary sensors
            assert mock_sensor_class.call_count == 6

            calls = mock_sensor_class.call_args_list

            # Check engineering info sensors (first 4)
            engineering_info_calls = calls[0:4]
            for call in engineering_info_calls:
                args, kwargs = call
                assert kwargs['command_type'] == "0x34"  # Engineering info command
                assert kwargs['device_class'] == BinarySensorDeviceClass.RUNNING

            # Check bit masks for engineering info
            assert calls[0][1]['bit_mask'] == 128  # pre_wash
            assert calls[1][1]['bit_mask'] == 64   # washing
            assert calls[2][1]['bit_mask'] == 32   # rinse
            assert calls[3][1]['bit_mask'] == 16   # spin

            # Detergent flag sits between the stage bits and remote control
            args, kwargs = calls[4]
            assert kwargs['command_type'] == "0x71"
            assert kwargs['sensor_key'] == "detergent_low"
            assert kwargs['bit_mask'] == 0x0100

            # Check remote control sensor (last one)
            args, kwargs = calls[5]
            assert kwargs['command_type'] == "0x74"
            assert kwargs['sensor_key'] == "remote_control_allowed"
            # Panel permission is not connectivity; it is a diagnostic flag
            assert 'device_class' not in kwargs
            assert kwargs['entity_category'] == EntityCategory.DIAGNOSTIC

    def test_engineering_info_sensor_keys(self, washing_machine_device, mock_coordinator):
        """Test that engineering info binary sensors have correct sensor keys."""
        with patch('custom_components.panasonic_iot_tw.binary_sensor.PanasonicBinarySensor') as mock_sensor_class:
            mock_sensor_instance = Mock()
            mock_sensor_class.return_value = mock_sensor_instance

            sensors = washing_machine_device.get_binary_sensor_entities(mock_coordinator)

            calls = mock_sensor_class.call_args_list

            # Check sensor keys for engineering info
            assert calls[0][1]['sensor_key'] == "prewash_status"
            assert calls[1][1]['sensor_key'] == "washing_status"
            assert calls[2][1]['sensor_key'] == "rinsing_status"
            assert calls[3][1]['sensor_key'] == "spinning_status"

    def test_empty_entity_methods(self, washing_machine_device, mock_coordinator):
        """Test that unsupported entity types return empty lists."""
        assert washing_machine_device.get_switch_entities(mock_coordinator) == []
        assert washing_machine_device.get_select_entities(mock_coordinator) == []
        assert washing_machine_device.get_number_entities(mock_coordinator) == []
        assert washing_machine_device.get_climate_entities(mock_coordinator) == []
        assert washing_machine_device.get_humidifier_entities(mock_coordinator) == []
        assert washing_machine_device.get_button_entities(mock_coordinator) == []

    def test_sensor_inheritance_pattern(self, washing_machine_device):
        """Test that washing machine properly inherits from base device."""
        # This tests the inherited methods from StatusReader and BaseDevice
        assert hasattr(washing_machine_device, 'get_int_status')
        assert hasattr(washing_machine_device, 'get_boolean_status')
        assert hasattr(washing_machine_device, 'get_status_value')
        assert hasattr(washing_machine_device, 'device_data')

    def test_device_data_property(self, washing_machine_device, mock_device_data):
        """Test that device_data property returns correct data."""
        device_data = washing_machine_device.device_data

        # Should preserve all original fields
        assert device_data["device_id"] == mock_device_data["device_id"]
        assert device_data["nickname"] == mock_device_data["nickname"]
        assert device_data["model"] == mock_device_data["model"]
        assert device_data["version"] == mock_device_data["version"]
        assert device_data["device_type"] == mock_device_data["device_type"]
        assert device_data["available"] == mock_device_data["available"]

    def test_remote_control_sensor_configuration(self, washing_machine_device, mock_coordinator):
        """Test that remote control sensor has special value processor."""
        with patch('custom_components.panasonic_iot_tw.binary_sensor.PanasonicBinarySensor') as mock_sensor_class:
            mock_sensor_instance = Mock()
            mock_sensor_class.return_value = mock_sensor_instance

            sensors = washing_machine_device.get_binary_sensor_entities(mock_coordinator)

            # Check remote control sensor (last call)
            remote_control_call = mock_sensor_class.call_args_list[-1]
            args, kwargs = remote_control_call

            # Should have value_processor for remote control
            assert 'value_processor' in kwargs

    @pytest.mark.parametrize("bit_value,bit_mask,expected_result", [
        (208, 128, True),   # pre_wash active (208 = 11010000, bit 128 is set)
        (208, 64, True),    # washing active (208 = 11010000, bit 64 is set)
        (208, 32, False),   # rinse inactive (208 = 11010000, bit 32 is not set)
        (208, 16, True),    # spin active (208 = 11010000, bit 16 is set)
        (0, 128, False),    # all inactive
        (255, 128, True),   # all active
    ])
    def test_bitwise_sensor_logic(self, bit_value, bit_mask, expected_result):
        """Test the bitwise logic for engineering info sensors."""
        # This tests the underlying bitwise logic that would be used
        result = bool(bit_value & bit_mask)
        assert result == expected_result

    def test_translation_keys(self, washing_machine_device, mock_coordinator):
        """Test that all sensors have proper translation keys."""
        with patch('custom_components.panasonic_iot_tw.sensor.PanasonicSensor') as mock_sensor_class, \
             patch('custom_components.panasonic_iot_tw.binary_sensor.PanasonicBinarySensor') as mock_binary_sensor_class:

            mock_sensor_instance = Mock()
            mock_sensor_class.return_value = mock_sensor_instance
            mock_binary_sensor_class.return_value = mock_sensor_instance

            # Test sensor translation keys
            sensors = washing_machine_device.get_sensor_entities(mock_coordinator)
            sensor_calls = mock_sensor_class.call_args_list

            assert sensor_calls[0][1]['translation_key'] == "washing_machine_washing_remaining_time"
            assert sensor_calls[1][1]['translation_key'] == "washing_machine_schedule_remaining_time"
            assert sensor_calls[2][1]['translation_key'] == "washing_machine_operation_status"
            assert sensor_calls[3][1]['translation_key'] == "washing_machine_cycle_message"

            # Reset mock
            mock_binary_sensor_class.reset_mock()

            # Test binary sensor translation keys
            binary_sensors = washing_machine_device.get_binary_sensor_entities(mock_coordinator)
            binary_calls = mock_binary_sensor_class.call_args_list

            expected_binary_keys = [
                "washing_machine_prewash_status",
                "washing_machine_washing_status",
                "washing_machine_rinsing_status",
                "washing_machine_spinning_status",
                "washing_machine_detergent_low",
                "washing_machine_remote_control_allowed"
            ]

            for i, expected_key in enumerate(expected_binary_keys):
                assert binary_calls[i][1]['translation_key'] == expected_key

    def test_device_info_inheritance(self, washing_machine_device):
        """Test that device info is properly inherited from BaseDevice."""
        device_info = washing_machine_device.get_device_info()

        assert device_info["identifiers"] == {("panasonic_iot_tw", "washing_machine_test_001")}
        assert device_info["name"] == "測試洗衣機"
        assert device_info["manufacturer"] == "Panasonic"
        assert device_info["model"] == "Test Washing Machine Model"