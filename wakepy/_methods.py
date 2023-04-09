from __future__ import annotations

from dataclasses import dataclass
import enum
import typing
import logging
import platform
import warnings
from .exceptions import KeepAwakeError
from .constants import System, CURRENT_SYSTEM

# from .._implementations._windows import methods as windows_methods
# from ._implementations._linux import methods as linux_methods
# from .._implementations._darwin import methods as darwin_methods

if typing.TYPE_CHECKING:
    from ._methods import KeepawakeMethod


def get_methods_for_system(system: System | None = None) -> list[KeepawakeMethod]:
    import warnings

    warnings.warn("Not implemented win & darwin yet")
    system = system or CURRENT_SYSTEM

    return {
        # System.WINDOWS: windows_methods,
        System.LINUX: ["dbus", "libdbus"],
        # System.DARWIN: darwin_methods,
    }.get(system, [])


def get_default_method_names_for_system(system: System | None = None) -> list[str]:
    system = system or CURRENT_SYSTEM
    methods = get_methods_for_system(system)
    return [x.name for x in methods]


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


@dataclass(kw_only=True)
class KeepawakeMethod:
    shortname: str
    printname: str
    set_keepawake: typing.Callable
    unset_keepawake: typing.Callable
    requirements: list[str] | None = None
    short_description: str = ""
