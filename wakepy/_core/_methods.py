from __future__ import annotations

from dataclasses import dataclass
import enum
import typing
import logging
import platform
import warnings
from ..exceptions import KeepAwakeError

# from .._implementations._windows import methods as windows_methods
from .._implementations._linux import methods as linux_methods

# from .._implementations._darwin import methods as darwin_methods

if typing.TYPE_CHECKING:
    from ._methods import KeepawakeMethod


class System(str, enum.Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"


CURRENT_SYSTEM = platform.system().lower()
SUPPORTED_SYSTEMS = list(x.value for x in System.__members__.values())


def get_methods_for_current_system() -> list[KeepawakeMethod]:
    return {
        # System.WINDOWS: windows_methods,
        System.LINUX: linux_methods,
        # System.DARWIN: darwin_methods,
    }.get(CURRENT_SYSTEM, [])


def get_default_method_names_for_current_system() -> list[str]:
    methods = get_methods_for_current_system()
    return [x.name for x in methods]


def get_method_names_from_args_for_current_system(
    method_win=None | str | list[str],
    method_linux=None | str | list[str],
    method_mac=None | str | list[str],
) -> list[str]:
    if CURRENT_SYSTEM not in SUPPORTED_SYSTEMS:
        return []

    methodnames = {
        System.WINDOWS: method_win,
        System.LINUX: method_linux,
        System.DARWIN: method_mac,
    }.get(CURRENT_SYSTEM)

    if methodnames is None:
        methodnames = get_default_method_names_for_current_system()
    elif isinstance(methodnames, str):
        methodnames = [methodnames]
    return methodnames


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


class KeepAwakeMethodExecutor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def handle_failure(
        self,
        exception: Exception,
        on_failure: OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    ):
        if on_failure == OnFailureStrategyName.PASS:
            return
        elif on_failure == OnFailureStrategyName.ERROR:
            raise exception
        elif on_failure == OnFailureStrategyName.WARN:
            warnings.warn(str(exception))
        elif on_failure == OnFailureStrategyName.PRINT:
            print(str(exception))
        elif on_failure == OnFailureStrategyName.LOGERROR:
            self.logger.error(str(exception))
        elif on_failure == OnFailureStrategyName.LOGWARN:
            self.logger.warning(str(exception))
        elif on_failure == OnFailureStrategyName.LOGINFO:
            self.logger.info(str(exception))
        elif on_failure == OnFailureStrategyName.LOGDEBUG:
            self.logger.debug(str(exception))
        elif on_failure == OnFailureStrategyName.CALLABLE:
            NotImplementedError("Using callables on failure not implemented")
        else:
            raise ValueError(
                f'Could not understand option: "on_failure = {on_failure}"'
            )

    def call_set_keepawake(
        self,
        method: KeepawakeMethod,
        on_failure: OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
        keep_screen_awake=False,
    ):
        try:
            method.set_keepawake(keep_screen_awake=keep_screen_awake)
        except KeepAwakeError as exception:
            self.handle_failure(exception, on_failure=on_failure)

    def call_unset_keepawake(
        self,
        method: KeepawakeMethod,
        on_failure: OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    ):
        try:
            method.unset_keepawake()
        except KeepAwakeError as exception:
            self.handle_failure(exception, on_failure=on_failure)


@dataclass
class KeepawakeMethod:
    shortname: str
    printname: str
    set_keepawake: typing.Callable
    unset_keepawake: typing.Callable
