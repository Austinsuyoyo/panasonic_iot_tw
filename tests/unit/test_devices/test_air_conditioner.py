# -*- coding: utf-8 -*-
"""Unit tests for air conditioner device implementation."""
import pytest
from unittest.mock import Mock, patch
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature

from custom_components.panasonic_iot_tw.devices.air_conditioner import AirConditionerDevice


class TestAirConditionerDevice:
    """Test cases for AirConditionerDevice class."""

    @pytest.fixture
    def mock_coordinator(self):
        """Create a mock coordinator with air conditioner data."""
        coordinator = Mock()
        coordinator.data = {
            0: {
                "status": {
                    "0x00": 1,    # Power: on
                    "0x01": 0,    # Mode: cool
                    "0x02": 3,    # Fan level: 3
                    "0x03": 24,   # Target temperature: 24C
                    "0x04": 26,   # Current temperature: 26C
                    "0x05": 0,    # Sleep mode: off
                    "0x08": 1,    # Nanoe: on
                    "0x0F": 2,    # Horizontal swing: position 2
                    "0x11": 1,    # Vertical swing: position 1
                    "0x1B": 1,    # ECONAVI: on
                    "0x21": 30,   # Outdoor temperature: 30C
                    "0x37": 15,   # PM2.5: 15 ug/m3
                }
            }
        }
        coordinator.last_update_success = True
        return coordinator

    @pytest.fixture
    def mock_device_data(self):
        """Create mock device data."""
        return {
            "device_id": "ac_test_001",
            "nickname": "Test AC",
            "model": "Test AC Model",
            "version": "1.0.0",
            "available": True,
            "device_type": 1,
        }

    @pytest.fixture
    def ac_device(self, mock_coordinator, mock_device_data):
        """Create an AirConditionerDevice instance for testing."""
        return AirConditionerDevice(mock_coordinator, 0, mock_device_data)

    def test_device_initialization(self, ac_device, mock_device_data):
        """Test proper device initialization."""
        assert ac_device.device_key == 0
        assert ac_device._device_data == mock_device_data
        assert ac_device.device_id == "ac_test_001"
        assert ac_device.model == "Test AC Model"

    def test_command_constants(self):
        """Test that all command constants are properly defined."""
        assert AirConditionerDevice.POWER_COMMAND == "0x00"
        assert AirConditionerDevice.MODE_COMMAND == "0x01"
        assert AirConditionerDevice.FAN_COMMAND == "0x02"
        assert AirConditionerDevice.TARGET_TEMP_COMMAND == "0x03"
        assert AirConditionerDevice.CURRENT_TEMP_COMMAND == "0x04"
        assert AirConditionerDevice.SLEEP_MODE_COMMAND == "0x05"
        assert AirConditionerDevice.NANOE_COMMAND == "0x08"
        assert AirConditionerDevice.HORIZONTAL_SWING_COMMAND == "0x0F"
        assert AirConditionerDevice.VERTICAL_SWING_COMMAND == "0x11"
        assert AirConditionerDevice.ECONAVI_COMMAND == "0x1B"
        assert AirConditionerDevice.OUTDOOR_TEMP_COMMAND == "0x21"
        assert AirConditionerDevice.PM25_COMMAND == "0x37"

    def test_mode_mapping(self):
        """Test that mode mapping is properly defined."""
        expected_modes = {
            0: "cool",
            1: "dry",
            2: "fan_only",
            3: "auto",
            4: "heat",
        }
        assert AirConditionerDevice.MODE_MAPPING == expected_modes

    def test_is_on_property(self, ac_device):
        """Test is_on property returns correct value."""
        assert ac_device.is_on is True

    def test_current_temperature_property(self, ac_device):
        """Test current_temperature property returns correct value."""
        assert ac_device.current_temperature == 26.0

    def test_target_temperature_property(self, ac_device):
        """Test target_temperature property returns correct value."""
        assert ac_device.target_temperature == 24.0

    def test_outdoor_temperature_property(self, ac_device):
        """Test outdoor_temperature property returns correct value."""
        assert ac_device.outdoor_temperature == 30.0

    def test_current_mode_property(self, ac_device):
        """Test current_mode property returns correct value."""
        assert ac_device.current_mode == "cool"

    def test_fan_level_property(self, ac_device):
        """Test fan_level property returns correct value."""
        assert ac_device.fan_level == 3

    def test_horizontal_swing_position_property(self, ac_device):
        """Test horizontal_swing_position property returns correct value."""
        assert ac_device.horizontal_swing_position == 2

    def test_vertical_swing_position_property(self, ac_device):
        """Test vertical_swing_position property returns correct value."""
        assert ac_device.vertical_swing_position == 1

    def test_is_nanoe_enabled_property(self, ac_device):
        """Test is_nanoe_enabled property returns correct value."""
        assert ac_device.is_nanoe_enabled is True

    def test_is_econavi_enabled_property(self, ac_device):
        """Test is_econavi_enabled property returns correct value."""
        assert ac_device.is_econavi_enabled is True

    def test_is_sleep_mode_enabled_property(self, ac_device):
        """Test is_sleep_mode_enabled property returns correct value."""
        assert ac_device.is_sleep_mode_enabled is False

    def test_pm25_level_property(self, ac_device):
        """Test pm25_level property returns correct value."""
        assert ac_device.pm25_level == 15

    def test_get_status_summary(self, ac_device):
        """Test status summary contains all expected fields."""
        summary = ac_device.get_status_summary()

        assert summary["power"] is True
        assert summary["mode"] == "cool"
        assert summary["current_temperature"] == 26.0
        assert summary["target_temperature"] == 24.0
        assert summary["outdoor_temperature"] == 30.0
        assert summary["fan_level"] == 3
        assert summary["nanoe_enabled"] is True
        assert summary["econavi_enabled"] is True
        assert summary["sleep_mode"] is False
        assert summary["pm25"] == 15
        assert "available" in summary

    def test_get_sensor_entities_count(self, ac_device, mock_coordinator):
        """Test that get_sensor_entities returns correct number of sensors."""
        sensors = ac_device.get_sensor_entities(mock_coordinator)
        # Should have at least 2 temperature sensors
        assert len(sensors) >= 2

    def test_get_sensor_entities_types(self, ac_device, mock_coordinator):
        """Test that sensor entities have correct types and properties."""
        with patch('custom_components.panasonic_iot_tw.sensor.PanasonicSensor') as mock_sensor_class:
            mock_sensor_instance = Mock()
            mock_sensor_class.return_value = mock_sensor_instance

            sensors = ac_device.get_sensor_entities(mock_coordinator)

            # Should create at least 2 sensors
            assert mock_sensor_class.call_count >= 2

            # Check specific sensor configurations
            calls = mock_sensor_class.call_args_list

            # Find current temperature sensor
            current_temp_call = next(
                (call for call in calls if call[1].get('command_type') == "0x04"),
                None
            )
            assert current_temp_call is not None
            _, kwargs = current_temp_call
            assert kwargs['sensor_key'] == "current_temperature"
            assert kwargs['device_class'] == SensorDeviceClass.TEMPERATURE
            assert kwargs['unit'] == UnitOfTemperature.CELSIUS

            # Find outdoor temperature sensor
            outdoor_temp_call = next(
                (call for call in calls if call[1].get('command_type') == "0x21"),
                None
            )
            assert outdoor_temp_call is not None
            _, kwargs = outdoor_temp_call
            assert kwargs['sensor_key'] == "outdoor_temperature"
            assert kwargs['device_class'] == SensorDeviceClass.TEMPERATURE
            assert kwargs['unit'] == UnitOfTemperature.CELSIUS

    def test_get_climate_entities(self, ac_device, mock_coordinator):
        """Test that get_climate_entities method exists."""
        # Air conditioner should have get_climate_entities method
        assert hasattr(ac_device, 'get_climate_entities')
        assert callable(getattr(ac_device, 'get_climate_entities'))
