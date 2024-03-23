"""Common terms and definitions used in many places"""

import sys

from .strenum import StrEnum, auto

if sys.version_info < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal


class PlatformName(StrEnum):
    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()
    OTHER = auto()


PlatformNameValue = Literal["WINDOWS", "LINUX", "MACOS", "OTHER"]


class ModeName(StrEnum):
    """The names of the modes wakepy supports

    See: wakepy/modes/keep.py for full definitions of the modes.
    """

    KEEP_RUNNING = "keep.running"
    KEEP_PRESENTING = "keep.presenting"


ModeNameValue = Literal["keep.running", "keep.presenting"]


class BusType(StrEnum):
    """Type of D-Bus bus."""

    SESSION = auto()
    SYSTEM = auto()


BusTypeValue = Literal["SESSION", "SYSTEM"]
