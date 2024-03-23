import sys

from wakepy.core import BusType, ModeName, PlatformName
from wakepy.core.constants import BusTypeValue, ModeNameValue, PlatformNameValue

if sys.version_info < (3, 8):
    import typing_extensions as typing
else:
    import typing


def test_platformname():
    """Tests that PlatformNameValue is in synch with PlatformName"""
    assert set(typing.get_args(PlatformNameValue)) == {
        member.value for member in PlatformName
    }


def test_modename():
    """Tests that ModeNameValue is in synch with ModeName"""
    assert set(typing.get_args(ModeNameValue)) == {member.value for member in ModeName}


def test_bustype():
    """Tests that BusTypeValue is in synch with BusType"""
    assert set(typing.get_args(BusTypeValue)) == {member.value for member in BusType}
