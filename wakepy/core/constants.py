"""Common terms and definitions used in many places"""
from .strenum import StrEnum, auto


class SystemName(StrEnum):
    """The names of supported systems"""

    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"


class ControlMsg(StrEnum):
    """Send to worker threads"""

    TERMINATE = auto()


class WorkerThreadMsgType(StrEnum):
    """Send from worker threads"""

    OK = auto()
    EXCEPTION = auto()
