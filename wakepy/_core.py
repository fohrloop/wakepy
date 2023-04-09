from __future__ import annotations

from dataclasses import dataclass
import typing
import logging
import platform


import warnings
from .exceptions import KeepAwakeError
from .constants import SystemName, CURRENT_SYSTEM, OnFailureStrategyName

# from .._implementations._windows import methods as windows_methods
# from ._implementations._linux import methods as linux_methods
# from .._implementations._darwin import methods as darwin_methods

CURRENT_SYSTEM = platform.system().lower()


warnings.warn("Not implemented win & darwin yet")
DEFAULT_METHODS = {
    # System.WINDOWS: windows_methods,
    SystemName.LINUX: ["dbus", "libdbus"],
    # System.DARWIN: darwin_methods,
}


def get_methods_for_system(system: SystemName | None = None) -> list[str]:
    system = system or CURRENT_SYSTEM
    return DEFAULT_METHODS.get(system, [])


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