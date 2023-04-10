from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
import inspect
import logging
import platform

import warnings
from .exceptions import KeepAwakeError
from .constants import (
    SystemName,
    OnFailureStrategyName,
    KeepAwakeModuleFunctionName,
    MethodNameLinux,
    MethodNameMac,
    MethodNameWindows,
)


logger = logging.getLogger(__name__)

CURRENT_SYSTEM = platform.system().lower()

# Defines the default methods and their order for each supported system
DEFAULT_METHODS = {
    SystemName.WINDOWS: [MethodNameWindows.ES_FLAGS],
    SystemName.LINUX: [
        MethodNameLinux.DBUS,
        MethodNameLinux.LIBDBUS,
        MethodNameLinux.SYSTEMD,
    ],
    SystemName.DARWIN: [MethodNameMac.CAFFEINATE],
}


class KeepawakeMethod:
    """instances of this class represent one module from
    wakepy._implementations._{system}._{method}
    """

    def __init__(
        self,
        system: str,
        method: str,
    ):
        """The input arguments define which module from
        wakepy._implementations to import.

        One module <--> one method

        Modules can define additional (debug/log) information
        about them in module level constants like PRINT_NAME
        and REQUIREMENTS
        """
        self.system = system

        try:
            self.module = import_module_for_method(system, method)
        except ModuleNotFoundError as e:
            raise KeepAwakeError(
                'No python module found for system "{system}" and method "{method}"'
            ) from e

        self.shortname = method
        self.printname: str = getattr(self.module, "PRINT_NAME", self.shortname)
        self.requirements: list[str] = getattr(self.module, "REQUIREMENTS", [])

    def call(self, func: KeepAwakeModuleFunctionName | str, **func_kwargs):
        """Call a function of the keepawake method (module).
        Functions are typically 'set_keepawake' and 'unset_keepawake'.

        The `func_kwargs` is filtered so that only the kwargs that are
        understood by the function are passed.
        """
        function_to_be_called = getattr(self.module, func)

        if function_to_be_called is None:
            raise KeepAwakeError(
                f'There is no function "{func}" in module "{self.module.__file__}"'
            )

        # Pass only the arguments that the function understands
        sig = inspect.signature(function_to_be_called)
        func_kwargs_filtered = {
            k: v for k, v in func_kwargs.items() if k in sig.parameters
        }
        function_to_be_called(**func_kwargs_filtered)


@dataclass
class WakepyResponse:
    """Used as responses in core functions"""

    failure: bool = False
    failure_reason: str = ""
    method_used: str = ""


def get_methods_for_system(system: SystemName | None = None) -> list[str]:
    system = system or CURRENT_SYSTEM
    return DEFAULT_METHODS.get(system, [])


def handle_failure(
    exception: Exception,
    on_failure: OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
):
    if not isinstance(exception, KeepAwakeError):
        # Only KeepAwakeErrors should be raised. If something else is raised,
        # it is unexpected and most probably a bug.
        # Instead of simply crashing, log it and continue with normal error
        # handling.
        logger.exception(
            "Wakepy got unexcepted exception! Please submit a PR at: https://github.com/np-8/wakepy/issues"
        )

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


def import_module_for_method(system, method):
    return import_module(f".._implementations._{system}._{method}", "wakepy._core")


def call_a_keepawake_function_with_single_method(
    func: KeepAwakeModuleFunctionName,
    method: str,
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
    system: SystemName | None = None,
    **func_kwargs,
) -> WakepyResponse:
    """This function imports a module corresponding the sytem and method
    and calls the `func` (e.g. 'set_keepawake'), and handles possible errors
    with the strategy chosen in `on_failure`."""
    response = WakepyResponse(failure=False, method_used=method)
    try:
        keepawake_method = KeepawakeMethod(
            system=system,
            method=method,
        )
        keepawake_method.call(func, **func_kwargs)
    except Exception as exception:
        # Although only KeepAwakeErrors should be raised, handle any type of
        # exceptions here and write a log message if it is not a KeepAwakeError
        response.failure = True
        response.failure_reason = str(exception)
        handle_failure(exception, on_failure=on_failure)
    return response


def call_a_keepawake_function_with_methods(
    func: KeepAwakeModuleFunctionName,
    methods: list[str] | None,
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
    on_method_failure: str | OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    system: SystemName | None = None,
    **func_kwargs,
) -> WakepyResponse:
    """Calls one function (e.g. set or unset keepawake) from  modules
    spciefied by the `methods`.

    Parameters
    ----------
    func:
        A KeepAwakeModuleFunctionName (or a string). Possible values include:
        'set_keepawake', 'unset_keepawake'. This is the name of the function
        in the implementation module to call.
    methods:
        Specifies the modules to use for importing the `func`. If None, default
        list of module for the system is used.
    on_failure:
        Defines what to do if all the methods fail.
    on_method_fauilure:
        Defines what to do after a method fails.
    system:
        The system used. Used in testing.
    func_kwargs
        keyword arguments to be passed to `func`.
    """
    methods = methods or get_methods_for_system(system)
    failure_reasons = []

    for method in methods:
        res = call_a_keepawake_function_with_single_method(
            func=func,
            method=method,
            on_failure=on_method_failure,
            system=system,
            **func_kwargs,
        )

        if not res.failure:
            # no failure -> assuming a success and not trying other methods
            break
        failure_reasons.append((res.method_used, res.failure_reason))
    else:
        # no break means that all of the methods failed
        err_text = f"Could not call {str(func)}. Tried methods: {str(methods)} for system {system}."
        for method, failure_reason in failure_reasons:
            err_text += f"\n\n[{method}]: {failure_reason}"
        exception = KeepAwakeError(err_text)
        handle_failure(exception, on_failure=on_failure)
        res = WakepyResponse(failure=True)
    return res
