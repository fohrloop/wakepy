import enum


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


class MethodNameWindows(str, enum.Enum):
    """This contains all the windows methods
    Each method correspons to a module in the
    wakepy._implementations._windows package
    (underscore neglected)
    """

    ES_FLAGS = "esflags"


class MethodNameLinux(str, enum.Enum):
    """This contains all the linux methods
    Each method correspons to a module in the
    wakepy._implementations._linux package
    (underscore neglected)
    """

    DBUS = "dbus"
    LIBDBUS = "libdbus"
    SYSTEMD = "systemd"


class MethodNameMac(str, enum.Enum):
    """This contains all the MacOS methods
    Each method correspons to a module in the
    wakepy._implementations._darwin package
    (underscore neglected)
    """

    CAFFEINATE = "caffeinate"


SUPPORTED_SYSTEMS = list(x.value for x in SystemName.__members__.values())


DEFAULT_METHODS = {
    # System.WINDOWS: windows_methods,
    SystemName.LINUX: ["dbus", "libdbus"],
    # System.DARWIN: darwin_methods,
}
