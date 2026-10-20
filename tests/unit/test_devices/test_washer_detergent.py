"""Unit tests for the two dispenser flags decoded from register 0x71.

Bit 8 (0x0100) was set through three separate low-detergent events, in both
idle and running states, and cleared as soon as the tank was refilled - the
refilled reading was taken at the same cycle stage (0x34=16) that had
previously reported the bit set, so the value does not merely follow the
programme. The low byte tracks the softener tank the same way, as the vendor
app's own decoding splits the word into a detergent byte and a softener byte.

Register 0x72 packs the two dispenser amounts (detergent in the high byte,
softener in the low nibble) and gates both flags: the app hides a tank's
warning unless that tank's amount is non-zero, so a machine that never uses a
slot keeps its warning byte at 0. A closed gate reports unknown rather than
"no warning", which would otherwise read as "the tank is fine".
"""
import pytest
from unittest.mock import Mock

from homeassistant.components.binary_sensor import BinarySensorDeviceClass

from custom_components.panasonic_iot_tw.devices.washing_machine import WashingMachineDevice

DEVICE_DATA = {
    "device_id": "washer1",
    "nickname": "Test Washer",
    "model": "NA-VS120RW",
    "version": "1.0.0",
    "available": True,
}

# 0x72 = 512: detergent amount set, softener amount 0. Tests that are not about
# the gate default to this so the detergent flag is live.
DETERGENT_IN_USE = 512


def _sensors(status):
    coordinator = Mock()
    coordinator.last_update_success = True
    merged = {"0x72": DETERGENT_IN_USE, **status}
    coordinator.data = {"washer1": {**DEVICE_DATA, "status": merged}}
    device = WashingMachineDevice(coordinator, "washer1", DEVICE_DATA)
    return {
        e._attr_unique_id.split("washer1_", 1)[1]: e
        for e in device.get_binary_sensor_entities(coordinator)
    }


class TestDetergentLow:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            (256, True),    # 0x0100 - observed on every low-detergent event
            (0, False),     # observed right after refilling
            (512, False),   # a different bit alone must not trigger
            (768, True),    # 0x0300 - bit 8 set alongside another bit
        ],
    )
    def test_bit8_decodes_detergent(self, raw, expected):
        sensors = _sensors({"0x71": raw, "0x50": 2})
        assert sensors["detergent_low"].is_on is expected

    def test_is_a_problem_not_a_running_state(self):
        sensors = _sensors({"0x71": 0, "0x50": 0})
        assert sensors["detergent_low"].device_class is BinarySensorDeviceClass.PROBLEM

    def test_independent_of_operation_status(self):
        """The flag held across idle and running alike, so 0x50 must not gate it."""
        for operation_status in (0, 1, 2, 5):
            sensors = _sensors({"0x71": 256, "0x50": operation_status})
            assert sensors["detergent_low"].is_on is True

    def test_missing_register_is_none(self):
        sensors = _sensors({"0x50": 2})
        assert sensors["detergent_low"].is_on is None

    def test_not_read_from_the_state_tracking_register(self):
        """0x5A follows the operation status, not the tank - it must be ignored."""
        sensors = _sensors({"0x5A": 2, "0x71": 0, "0x50": 0})
        assert sensors["detergent_low"].is_on is False


class TestSoftenerLow:
    """The low byte of the same register, which the app calls softWarning."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            (0x0001, True),   # low byte 1 - softener low
            (0x0000, False),
            (0x0100, False),  # detergent's bit must not light the softener flag
            (0x0101, True),   # both tanks low
        ],
    )
    def test_low_byte_decodes_softener(self, raw, expected):
        sensors = _sensors({"0x71": raw, "0x72": 0x0103})
        assert sensors["softener_low"].is_on is expected

    def test_is_a_problem(self):
        sensors = _sensors({"0x71": 0, "0x72": 0x0103})
        assert sensors["softener_low"].device_class is BinarySensorDeviceClass.PROBLEM


class TestDispenserGate:
    """A tank warning only means something while its slot is in use (0x72)."""

    def test_softener_is_silent_while_the_slot_is_unused(self):
        """The reported case: a machine that never uses softener."""
        sensors = _sensors({"0x71": 0, "0x72": 512})
        assert sensors["softener_low"].is_on is None

    def test_softener_speaks_once_an_amount_is_set(self):
        sensors = _sensors({"0x71": 0, "0x72": 512 | 3})
        assert sensors["softener_low"].is_on is False

    def test_detergent_is_silent_while_the_slot_is_unused(self):
        sensors = _sensors({"0x71": 0x0100, "0x72": 0})
        assert sensors["detergent_low"].is_on is None

    def test_detergent_amount_of_zero_is_treated_as_unused(self):
        """The app zeroes the detergent amount at 1000 and above."""
        sensors = _sensors({"0x71": 0x0100, "0x72": 1024})
        assert sensors["detergent_low"].is_on is None

    def test_gate_is_not_the_operation_status(self):
        """0x50 still must not gate the tank flags."""
        sensors = _sensors({"0x71": 0x0100, "0x50": 0})
        assert sensors["detergent_low"].is_on is True

    def test_both_slots_in_use_lets_both_speak(self):
        sensors = _sensors({"0x71": 0x0101, "0x72": 512 | 3})
        assert sensors["detergent_low"].is_on is True
        assert sensors["softener_low"].is_on is True


def _level_sensors(status):
    coordinator = Mock()
    coordinator.last_update_success = True
    coordinator.data = {"washer1": {**DEVICE_DATA, "status": status}}
    device = WashingMachineDevice(coordinator, "washer1", DEVICE_DATA)
    return {
        e._attr_unique_id.split("washer1_", 1)[1]: e
        for e in device.get_sensor_entities(coordinator)
        if e._attr_unique_id.endswith(("_detergent_amount", "_softener_amount"))
    }


class TestDispenserLevels:
    """0x72 is the sum of the app's two amounts, and each is a level 0-3.

    The app sums its two dispenser amounts when a programme starts, so the
    detergent side lands in the high byte and the softener side in the low
    nibble. Its own picker labels the levels 無 / 較少 / 標準 / 較多 and stores
    the detergent side scaled by 256.
    """

    @pytest.mark.parametrize(
        "raw,detergent,softener",
        [
            (0, "none", "none"),
            (512, "normal", "none"),      # the machine under test: 標準 / 無
            (512 | 3, "normal", "more"),
            (256, "less", "none"),
            (768, "more", "none"),
            (0x0101, "less", "less"),     # 257 -> both at 較少
            (1024, "none", "none"),       # the app zeroes detergent from 1000 up
        ],
    )
    def test_levels_decode_from_the_word(self, raw, detergent, softener):
        sensors = _level_sensors({"0x71": 0, "0x72": raw})
        assert sensors["detergent_amount"].native_value == detergent
        assert sensors["softener_amount"].native_value == softener

    def test_levels_are_not_gated(self):
        """The level is a setting; it is meaningful whether or not a cycle runs."""
        sensors = _level_sensors({"0x72": 512, "0x50": 0})
        assert sensors["detergent_amount"].native_value == "normal"
        assert sensors["softener_amount"].native_value == "none"

    def test_missing_register_is_none(self):
        sensors = _level_sensors({"0x50": 2})
        assert sensors["detergent_amount"].native_value is None
