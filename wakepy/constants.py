import enum
import platform


class KeepAwakeModuleFunctionName(str, enum.Enum):
    """The names of the functions which may be called.

    The respective functions are expected to be present in the
    implementation module
    """

    SET_KEEPAWAKE = "set_keepawake"
    UNSET_KEEPAWAKE = "unset_keepawake"


class SystemName(str, enum.Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"


class OnFailureStrategyName(str, enum.Enum):
    ERROR = "error"
    WARN = "warn"
    PRINT = "print"
    LOGERROR = "logerror"
    LOGWARN = "logwarn"
    LOGINFO = "loginfo"
    LOGDEBUG = "logdebug"
    PASS = "pass"
    CALLABLE = "callable"


SUPPORTED_SYSTEMS = list(x.value for x in SystemName.__members__.values())
CURRENT_SYSTEM = platform.system().lower()
