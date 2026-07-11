"""Simplified unit tests for device factory implementation."""
import pytest
from unittest.mock import Mock, patch

from custom_components.panasonic_iot_tw.devices.device_factory import DeviceFactory, register_all_devices
from custom_components.panasonic_iot_tw.base.device_base import BaseDevice
from custom_components.panasonic_iot_tw.const import (
    DEVICE_TYPE_AC,
    DEVICE_TYPE_DRYER,
    DEVICE_TYPE_WASHING_MACHINE,
)


class TestDeviceFactoryCore:
    """Test core DeviceFactory functionality."""

    def setup_method(self):
        """Setup test environment before each test."""
        # Clear the device classes registry before each test
        DeviceFactory._device_classes = {}

    def test_register_device_class_basic(self):
        """Test basic device class registration."""
        mock_device_class = Mock()
        mock_device_class.__name__ = "TestDevice"

        DeviceFactory.register_device_class(DEVICE_TYPE_AC, mock_device_class)

        assert DEVICE_TYPE_AC in DeviceFactory._device_classes
        assert DeviceFactory._device_classes[DEVICE_TYPE_AC] == mock_device_class

    def test_create_device_success(self):
        """Test successful device creation."""
        mock_device_class = Mock()
        mock_device_instance = Mock(spec=BaseDevice)
        mock_device_class.return_value = mock_device_instance
        mock_device_class.__name__ = "TestDevice"

        DeviceFactory.register_device_class(DEVICE_TYPE_AC, mock_device_class)

        mock_coordinator = Mock()
        device_data = {"device_type": DEVICE_TYPE_AC, "nickname": "Test AC"}

        result = DeviceFactory.create_device(mock_coordinator, 0, device_data)

        assert result == mock_device_instance
        mock_device_class.assert_called_once_with(mock_coordinator, 0, device_data)

    def test_create_device_unregistered_type(self):
        """Test device creation with unregistered device type."""
        mock_coordinator = Mock()
        device_data = {"device_type": 999, "nickname": "Unknown Device"}

        result = DeviceFactory.create_device(mock_coordinator, 0, device_data)
        assert result is None

    def test_create_device_instantiation_failure(self):
        """Test device creation when instantiation fails."""
        mock_device_class = Mock()
        mock_device_class.side_effect = Exception("Creation failed")
        mock_device_class.__name__ = "FailingDevice"

        DeviceFactory.register_device_class(DEVICE_TYPE_AC, mock_device_class)

        mock_coordinator = Mock()
        device_data = {"device_type": DEVICE_TYPE_AC, "nickname": "Failing Device"}

        result = DeviceFactory.create_device(mock_coordinator, 0, device_data)
        assert result is None

    def test_get_supported_device_types(self):
        """Test getting supported device types."""
        mock_device_1 = Mock()
        mock_device_1.__name__ = "Device1"
        mock_device_2 = Mock()
        mock_device_2.__name__ = "Device2"

        assert DeviceFactory.get_supported_device_types() == []

        DeviceFactory.register_device_class(DEVICE_TYPE_AC, mock_device_1)
        DeviceFactory.register_device_class(DEVICE_TYPE_DRYER, mock_device_2)

        supported_types = DeviceFactory.get_supported_device_types()
        assert set(supported_types) == {DEVICE_TYPE_AC, DEVICE_TYPE_DRYER}

    def test_multiple_device_registration(self):
        """Test registering multiple device types."""
        device_types = [DEVICE_TYPE_AC, DEVICE_TYPE_DRYER, DEVICE_TYPE_WASHING_MACHINE]

        for i, device_type in enumerate(device_types):
            mock_device = Mock()
            mock_device.__name__ = f"Device{i}"
            DeviceFactory.register_device_class(device_type, mock_device)

        assert len(DeviceFactory.get_supported_device_types()) == 3
        assert all(dt in DeviceFactory.get_supported_device_types() for dt in device_types)


class TestRegisterAllDevicesSimple:
    """Simplified tests for register_all_devices function."""

    def setup_method(self):
        """Setup test environment before each test."""
        DeviceFactory._device_classes = {}

    def test_register_all_devices_with_mocked_devices(self):
        """Test register_all_devices with mocked device classes."""
        mock_dryer = Mock()
        mock_dryer.__name__ = "DryerDevice"

        with patch('custom_components.panasonic_iot_tw.devices.dryer.DryerDevice', mock_dryer):
            register_all_devices()

            # Should have registered at least the dryer
            supported_types = DeviceFactory.get_supported_device_types()
            assert DEVICE_TYPE_DRYER in supported_types

    def test_register_all_devices_import_error_handling(self):
        """Test that import errors are handled gracefully."""
        # This test runs the actual register_all_devices function
        # Some imports might fail but it should not crash
        initial_count = len(DeviceFactory.get_supported_device_types())

        try:
            register_all_devices()
            # Should complete without crashing
            final_count = len(DeviceFactory.get_supported_device_types())
            # Should have registered at least some devices (or none if all imports fail)
            assert final_count >= initial_count
        except Exception as e:
            pytest.fail(f"register_all_devices should not raise exceptions: {e}")

    def test_factory_state_preservation(self):
        """Test that factory state is preserved between operations."""
        mock_device = Mock()
        mock_device.__name__ = "TestDevice"

        # Manually register a device
        DeviceFactory.register_device_class(DEVICE_TYPE_AC, mock_device)
        count_before = len(DeviceFactory.get_supported_device_types())

        # Run register_all_devices
        register_all_devices()
        count_after = len(DeviceFactory.get_supported_device_types())

        # Original registration should be preserved
        assert DEVICE_TYPE_AC in DeviceFactory.get_supported_device_types()
        assert count_after >= count_before