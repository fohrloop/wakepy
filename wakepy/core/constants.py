"""Common terms and definitions used in many places"""
from .strenum import StrEnum, auto


class PlatformName(StrEnum):
    WINDOWS = auto()
    LINUX = auto()
    MACOS = auto()
    WSL = auto()
    OTHER = auto()


class ModeName(StrEnum):
    """The names of the modes wakepy supports

    See: wakepy/modes/keep.py for full definitions of the modes.
    """

    KEEP_RUNNING = "keep.running"
    KEEP_PRESENTING = "keep.presenting"


class BusType(StrEnum):
    """Type of D-Bus bus."""

    SESSION = auto()
    SYSTEM = auto()
