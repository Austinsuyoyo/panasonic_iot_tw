"""Phase decoding for the laundry engineering register (0x34) and tank flags (0x71).

Register 0x34 keeps one bit per phase of the running programme that has *not*
finished yet, clearing each bit as that phase completes. The phase being run is
therefore the highest bit still set, and the word reaches 0 when the programme
ends. The values asserted here are the ones recorded from the real appliances
(22k polls): the washer ran 112 -> 48 -> 16 -> 0 and the dryer 12 -> 4 with the
remaining time falling alongside.

"""
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.panasonic_iot_tw.base import value_processors
from custom_components.panasonic_iot_tw.binary_sensor import PanasonicBinarySensor
from custom_components.panasonic_iot_tw.const import (
    DRYER_AVAILABLE_PHASES,
    WASHING_MACHINE_AVAILABLE_PHASES,
)
from custom_components.panasonic_iot_tw.sensor import PanasonicSensor

DEVICE_KEY = "device-abc"

# Operation status (0x50) values used by the gate.
NOT_DISPLAYED = 0
RUNNING = 2
FINISHED = 5
GATE_ALLOWED = (RUNNING, FINISHED)

# The values the appliances actually reported, in programme order.
WASHER_SEQUENCE = [(112, "washing"), (48, "rinsing"), (16, "spinning"), (0, "finished")]
DRYER_SEQUENCE = [(12, "drying"), (4, "air_flow"), (0, "finished")]


def _make_coordinator(status, available=True):
    coordinator = Mock()
    coordinator.last_update_success = True
    coordinator.data = {
        DEVICE_KEY: {
            "device_id": DEVICE_KEY,
            "nickname": "Test Appliance",
            "model": "X",
            "available": available,
            "status": status,
        }
    }
    coordinator.async_request_refresh = AsyncMock()
    return coordinator


def _make_sensor(coordinator, command_type, processor, gate=False):
    device_data = {"device_id": DEVICE_KEY, "nickname": "Test Appliance", "model": "X"}
    return PanasonicSensor(
        coordinator,
        DEVICE_KEY,
        device_data,
        command_type,
        "Stage",
        "current_stage",
        value_processor=processor,
        gate_command="0x50" if gate else None,
        gate_allowed=GATE_ALLOWED,
    )


def _make_binary_sensor(
    coordinator, command_type, sensor_key, processor=None, bit_mask=None, gate=False
):
    device_data = {"device_id": DEVICE_KEY, "nickname": "Test Appliance", "model": "X"}
    return PanasonicBinarySensor(
        coordinator,
        DEVICE_KEY,
        device_data,
        command_type,
        "Flag",
        sensor_key,
        value_processor=processor,
        bit_mask=bit_mask,
        gate_command="0x50" if gate else None,
        gate_allowed=GATE_ALLOWED,
    )


class TestPendingPhaseWord:
    """The word names the phase in progress, not every phase still pending."""

    @pytest.mark.parametrize("packed,expected", WASHER_SEQUENCE)
    def test_washer_sequence(self, packed, expected):
        processor = value_processors.create_pending_phase_processor(
            WASHING_MACHINE_AVAILABLE_PHASES
        )
        assert processor(packed) == expected

    @pytest.mark.parametrize("packed,expected", DRYER_SEQUENCE)
    def test_dryer_sequence(self, packed, expected):
        processor = value_processors.create_pending_phase_processor(DRYER_AVAILABLE_PHASES)
        assert processor(packed) == expected

    def test_prewash_is_the_first_phase_when_the_programme_uses_it(self):
        processor = value_processors.create_pending_phase_processor(
            WASHING_MACHINE_AVAILABLE_PHASES
        )
        assert processor(128 | 64 | 32 | 16) == "prewash"
        assert processor(64 | 32 | 16) == "washing"

    def test_every_phase_is_mutually_exclusive(self):
        """The bug this fixes: all phases used to read active at once."""
        processor = value_processors.create_pending_phase_processor(
            WASHING_MACHINE_AVAILABLE_PHASES
        )
        matchers = {
            phase: value_processors.create_current_phase_matcher(
                WASHING_MACHINE_AVAILABLE_PHASES, phase
            )
            for phase in WASHING_MACHINE_AVAILABLE_PHASES.values()
        }
        for packed, _expected in WASHER_SEQUENCE:
            active = [phase for phase, match in matchers.items() if match(packed)]
            assert len(active) <= 1, f"{packed} reported {active} phases at once"
            assert len(set(active)) == len(active)
        # 112 must not light up every phase the way a raw bit test did.
        assert sum(bool(112 & mask) for mask in WASHING_MACHINE_AVAILABLE_PHASES) == 3

    def test_unreadable_word_declines_to_guess(self):
        processor = value_processors.create_pending_phase_processor(
            WASHING_MACHINE_AVAILABLE_PHASES
        )
        assert processor("nonsense") is None
        assert processor(None) is None


class TestStageEntity:
    """The entity only reports a phase while the programme is actually running."""

    def test_reports_the_phase_while_running(self):
        coordinator = _make_coordinator({"0x50": RUNNING, "0x34": 112})
        sensor = _make_sensor(
            coordinator,
            "0x34",
            value_processors.create_pending_phase_processor(WASHING_MACHINE_AVAILABLE_PHASES),
            gate=True,
        )
        assert sensor.native_value == "washing"

    def test_idle_word_does_not_leak_a_phase(self):
        """While idle the register still holds the whole programme's bits."""
        coordinator = _make_coordinator({"0x50": NOT_DISPLAYED, "0x34": 112})
        sensor = _make_sensor(
            coordinator,
            "0x34",
            value_processors.create_pending_phase_processor(WASHING_MACHINE_AVAILABLE_PHASES),
            gate=True,
        )
        assert sensor.native_value is None

    def test_finished_programme_reports_finished(self):
        coordinator = _make_coordinator({"0x50": FINISHED, "0x34": 0})
        sensor = _make_sensor(
            coordinator,
            "0x34",
            value_processors.create_pending_phase_processor(WASHING_MACHINE_AVAILABLE_PHASES),
            gate=True,
        )
        assert sensor.native_value == "finished"

    def test_faulted_programme_does_not_claim_a_phase(self):
        """0x50 = 8 leaves the spin bit set but the machine has stopped."""
        coordinator = _make_coordinator({"0x50": 8, "0x34": 16})
        sensor = _make_sensor(
            coordinator,
            "0x34",
            value_processors.create_pending_phase_processor(WASHING_MACHINE_AVAILABLE_PHASES),
            gate=True,
        )
        assert sensor.native_value is None


class TestPhaseBinarySensorsAreGated:
    """Regression: the per-phase binary sensors passed gate arguments that the
    binary sensor platform silently ignored, so an idle machine would have
    reported a phase. The gate now lives on the shared entity base."""

    def test_idle_machine_reports_no_phase(self):
        coordinator = _make_coordinator({"0x50": NOT_DISPLAYED, "0x34": 112})
        sensors = {
            phase: _make_binary_sensor(
                coordinator,
                "0x34",
                phase,
                processor=value_processors.create_current_phase_matcher(
                    WASHING_MACHINE_AVAILABLE_PHASES, phase
                ),
                gate=True,
            )
            for phase in WASHING_MACHINE_AVAILABLE_PHASES.values()
        }
        assert all(sensor.is_on is None for sensor in sensors.values())

    def test_running_machine_lights_exactly_one_phase(self):
        coordinator = _make_coordinator({"0x50": RUNNING, "0x34": 112})
        sensors = {
            phase: _make_binary_sensor(
                coordinator,
                "0x34",
                phase,
                processor=value_processors.create_current_phase_matcher(
                    WASHING_MACHINE_AVAILABLE_PHASES, phase
                ),
                gate=True,
            )
            for phase in WASHING_MACHINE_AVAILABLE_PHASES.values()
        }
        active = [phase for phase, sensor in sensors.items() if sensor.is_on]
        assert active == ["washing"]

