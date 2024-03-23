"""Common terms and definitions used in many places"""

import typing

from .strenum import StrEnum, auto


class PlatformName(StrEnum):
    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()
    OTHER = auto()


PlatformNameValue = typing.Literal["WINDOWS", "LINUX", "MACOS", "OTHER"]


class ModeName(StrEnum):
    """The names of the modes wakepy supports

    See: wakepy/modes/keep.py for full definitions of the modes.
    """

    KEEP_RUNNING = "keep.running"
    KEEP_PRESENTING = "keep.presenting"


ModeNameValue = typing.Literal["keep.running", "keep.presenting"]


class BusType(StrEnum):
    """Type of D-Bus bus."""

    SESSION = auto()
    SYSTEM = auto()


BusTypeValue = typing.Literal["SESSION", "SYSTEM"]
