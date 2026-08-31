"""The raw-register sensors must expose every bit the appliances actually use."""
from custom_components.panasonic_iot_tw.base.value_processors import (
    STATUS_FLAG_BIT_WIDTH,
    process_status_flag_bits,
)


def test_covers_the_widest_observed_register():
    """0x66 read 33320 during a door alarm - bit 15 must be reachable."""
    attrs = process_status_flag_bits(33320)
    assert attrs["raw_value"] == 33320
    assert attrs["bit_15"] is True
    assert attrs["bit_3"] is True
    assert attrs["bit_0"] is False


def test_covers_the_laundry_register():
    """The dryer's 0x75 read 1024 while the filter reminder was showing."""
    attrs = process_status_flag_bits(1024)
    assert attrs["bit_10"] is True
    assert sum(1 for k, v in attrs.items() if k.startswith("bit_") and v) == 1


def test_every_bit_is_published():
    attrs = process_status_flag_bits(0)
    bits = [k for k in attrs if k.startswith("bit_")]
    assert len(bits) == STATUS_FLAG_BIT_WIDTH == 16
    assert attrs["binary"] == "0b" + "0" * 16
