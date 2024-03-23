from wakepy.core import BusType, ModeName, PlatformName
from wakepy.core.constants import BusTypeValue, ModeNameValue, PlatformNameValue


def test_platformname(assert_strenum_values):
    assert_strenum_values(PlatformName, PlatformNameValue)


def test_modename(assert_strenum_values):
    assert_strenum_values(ModeName, ModeNameValue)


def test_bustype(assert_strenum_values):
    assert_strenum_values(BusType, BusTypeValue)
