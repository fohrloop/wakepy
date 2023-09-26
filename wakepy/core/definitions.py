"""Common terms and definitions used in many places"""
from .constant import StringConstant, auto


class SystemName(StringConstant):
    """The names of supported systems"""

    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"


class ControlMsg(StringConstant):
    """Send to worker threads"""

    TERMINATE = auto()


class WorkerThreadMsgType(StringConstant):
    """Send from worker threads"""

    OK = auto()
    EXCEPTION = auto()
