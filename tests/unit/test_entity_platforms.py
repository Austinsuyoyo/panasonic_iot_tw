"""Entity platforms against the Home Assistant release the tests run on.

Deprecated API usage is caught by the autouse _fail_on_ha_deprecation fixture
in conftest.py; these tests make sure every platform actually exercises it,
including the device types no test account owns (AC, dehumidifier, ...).
"""
import importlib
import inspect
import logging
import pkgutil
from unittest.mock import AsyncMock, Mock, call, patch

import pytest
from homeassistant.components.climate import ClimateEntityFeature
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
from pytest_homeassistant.common import MockConfigEntry

import custom_components.panasonic_iot_tw as integration
from custom_components.panasonic_iot_tw.const import (
    DEVICE_TYPE_AC,
    DOMAIN,
)
from custom_components.panasonic_iot_tw.devices.device_factory import (
    DeviceFactory,
    register_all_devices,
)


def _device(device_type, status=None):
    device_id = f"dev-{device_type}"
    return device_id, {
        "device_id": device_id,
        "nickname": f"Device {device_type}",
        "available": True,
        "device_type": device_type,
        "status": status or {},
    }


async def _setup(hass, devices):
    """Set up the integration with a fake SmartApp serving ``devices``."""
    smart_app = AsyncMock()
    smart_app.set_initialization_mode = Mock()
    smart_app.get_device_with_info.return_value = dict(devices)
    smart_app.set_device_command.return_value = True
    entry = MockConfigEntry(domain=DOMAIN, data={"username": "u", "password": "p"}, version=2)
    entry.add_to_hass(hass)
    with patch("custom_components.panasonic_iot_tw.SmartApp", return_value=smart_app):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    return entry, smart_app


def _entity_classes():
    """Every Entity subclass defined anywhere in the integration package."""
    for info in pkgutil.walk_packages(integration.__path__, f"{integration.__name__}."):
        module = importlib.import_module(info.name)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, Entity) and cls.__module__ == module.__name__:
                yield cls


def test_entity_classes_use_current_entity_api():
    """Subclass every entity class so HA's class-definition deprecation checks run again.

    Those checks run in __init_subclass__, i.e. at import, which happens during
    collection where no test can see the report. A throwaway subclass repeats
    them without reloading modules (which would swap the class objects other
    tests imported).
    """
    classes = list(_entity_classes())
    assert {cls.__name__ for cls in classes} >= {"PanasonicClimate", "PanasonicSensor"}
    for cls in classes:
        type(f"_Probe{cls.__name__}", (cls,), {})


async def test_every_device_type_sets_up_cleanly(hass: HomeAssistant, caplog):
    """One device of every registered type loads all platforms without errors."""
    register_all_devices()
    device_types = DeviceFactory.get_supported_device_types()
    entry, _ = await _setup(hass, [_device(t) for t in device_types])

    assert entry.state is ConfigEntryState.LOADED
    errors = [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]
    assert not errors, errors
    assert hass.states.async_entity_ids("climate")


@pytest.mark.parametrize(("power", "expected_state"), [("1", "cool"), ("0", "off")])
async def test_climate_reads_state(hass: HomeAssistant, power, expected_state):
    """The climate entity reads the API's string statuses as integer degrees.

    Statuses arrive as strings, as DeviceGetInfo returns them. 0x03 is a
    16-30 range in whole degrees per the official app's CommandList (demo
    data in the APK, model CS-PX22A2).
    """
    device_id, ac = _device(DEVICE_TYPE_AC, {"0x00": power, "0x01": "0", "0x02": "3", "0x03": "24", "0x04": "26"})
    await _setup(hass, [(device_id, ac)])
    (entity_id,) = hass.states.async_entity_ids("climate")

    state = hass.states.get(entity_id)
    assert state.state == expected_state
    assert not state.attributes["supported_features"] & ClimateEntityFeature.SWING_MODE  # no swing command
    assert state.attributes["current_temperature"] == 26
    assert state.attributes["temperature"] == 24


async def test_climate_sends_commands(hass: HomeAssistant):
    """Service calls on a powered-off unit become the matching register writes."""
    device_id, ac = _device(DEVICE_TYPE_AC, {"0x00": "0", "0x01": "0", "0x02": "3", "0x03": "24", "0x04": "26"})
    _, smart_app = await _setup(hass, [(device_id, ac)])
    (entity_id,) = hass.states.async_entity_ids("climate")

    for service, data in (
        ("set_hvac_mode", {"hvac_mode": "heat"}),
        ("set_temperature", {"temperature": 25, "hvac_mode": "cool"}),
        ("turn_off", {}),
        ("turn_on", {}),
    ):
        await hass.services.async_call("climate", service, {"entity_id": entity_id, **data}, blocking=True)

    # The fake cloud keeps reporting power off, so each mode change powers on first
    assert smart_app.set_device_command.await_args_list == [
        call(device_id, "0x00", 1),
        call(device_id, "0x01", 4),  # heat
        call(device_id, "0x00", 1),
        call(device_id, "0x01", 0),  # cool, from set_temperature's hvac_mode
        call(device_id, "0x03", 25),
        call(device_id, "0x00", 0),
        call(device_id, "0x00", 1),  # power only, the mode is left alone
    ]


async def test_climate_in_fahrenheit_rounds_to_whole_degrees(hass: HomeAssistant):
    """HA converts °F to °C before calling us; the unit takes whole degrees only."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    device_id, ac = _device(DEVICE_TYPE_AC, {"0x00": "1", "0x01": "0", "0x02": "3", "0x03": "24", "0x04": "26"})
    _, smart_app = await _setup(hass, [(device_id, ac)])
    (entity_id,) = hass.states.async_entity_ids("climate")

    await hass.services.async_call(
        "climate", "set_temperature", {"entity_id": entity_id, "temperature": 75}, blocking=True
    )
    smart_app.set_device_command.assert_awaited_once_with(device_id, "0x03", 24)  # 23.89 °C, not truncated to 23
