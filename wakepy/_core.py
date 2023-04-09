from __future__ import annotations

from dataclasses import dataclass
import typing
import logging
import platform


import warnings
from .exceptions import KeepAwakeError
from .constants import (
    SystemName,
    CURRENT_SYSTEM,
    OnFailureStrategyName,
    KeepAwakeModuleFunctionName,
)

from .exceptions import KeepAwakeError


# from .._implementations._windows import methods as windows_methods
# from ._implementations._linux import methods as linux_methods
# from .._implementations._darwin import methods as darwin_methods

CURRENT_SYSTEM = platform.system().lower()
logger = logging.getLogger(__name__)

warnings.warn("Not implemented win & darwin yet")
DEFAULT_METHODS = {
    # System.WINDOWS: windows_methods,
    SystemName.LINUX: ["dbus", "libdbus"],
    # System.DARWIN: darwin_methods,
}


def get_methods_for_system(system: SystemName | None = None) -> list[str]:
    system = system or CURRENT_SYSTEM
    return DEFAULT_METHODS.get(system, [])


def handle_failure(
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
        logger.error(str(exception))
    elif on_failure == OnFailureStrategyName.LOGWARN:
        logger.warning(str(exception))
    elif on_failure == OnFailureStrategyName.LOGINFO:
        logger.info(str(exception))
    elif on_failure == OnFailureStrategyName.LOGDEBUG:
        logger.debug(str(exception))
    elif on_failure == OnFailureStrategyName.CALLABLE:
        NotImplementedError("Using callables on failure not implemented")
    else:
        raise ValueError(f'Could not understand option: "on_failure = {on_failure}"')


@dataclass
class WakepyResponse:
    failure: bool = False


def call_a_keepawake_function_with_single_method(
    func: KeepAwakeModuleFunctionName,
    method: str,
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
    system: SystemName | None = None,
) -> WakepyResponse:
    response = WakepyResponse()
    module = import_module(system, method)
    function_to_be_called = getattr(module, func)
    try:
        function_to_be_called()
        return
    except KeepAwakeError as exception:
        response.failure = True
        handle_failure(exception, on_failure=on_failure)
    return response


def call_a_keepawake_function(
    func: KeepAwakeModuleFunctionName,
    methods: list[str] | None,
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
    on_method_failure: str | OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    system: SystemName | None = None,
):
    """Calls one function (e.g. set or unset keepawake) from a specified module

    Parameters
    ----------
    func:
        A KeepAwakeModuleFunctionName (or a string). Possible values include:
        'set_keepawake', 'unset_keepawake'. This is the name of the function
        in the implementation module to call.

    """
    methods = methods or get_methods_for_system(system)

    # TODO: make this work
    for method in methods:
        res = call_a_keepawake_function_with_single_method(
            func=func,
            method=method,
            on_failure=on_method_failure,
            system=system,
        )
        if not res.failure:
            # no failure -> assuming a success and not trying other methods
            break
    else:
        # no break means that none of the methods worked.
        exception = KeepAwakeError(f"Could not call {str(func)}. Tried methods: ")
        handle_failure(exception, on_failure=on_failure)


@dataclass(kw_only=True)
class KeepawakeMethod:
    shortname: str
    printname: str
    set_keepawake: typing.Callable
    unset_keepawake: typing.Callable
    requirements: list[str] | None = None
    short_description: str = ""
