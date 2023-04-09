"""This module provides the following core functions of wakepy:

keepawake()
    A context manager that sets and unsets keepawake.

set_keepawake()
unset_keepawake()
    The lower level functions that can be used in any script to
    set or unset the keepawake.
"""

from __future__ import annotations

import enum
from contextlib import contextmanager


from ._methods import (
    KeepAwakeMethodExecutor,
    OnFailureStrategyName,
    System,
    CURRENT_SYSTEM,
    get_default_method_names_for_system,
)


class KeepAwakeModuleFunction(str, enum.Enum):
    """The different functions which may be called (tasks).

    The values are also the function names in the implementation module
    """

    SET_KEEPAWAKE = "set_keepawake"
    UNSET_KEEPAWAKE = "unset_keepawake"


def get_module_names(
    method_win=None | str | list[str],
    method_linux=None | str | list[str],
    method_mac=None | str | list[str],
    system: System | None = None,
):
    """Convert a method name to wakepy module name"""

    system = system or CURRENT_SYSTEM

    # Select the input argument based on system
    method = {
        System.WINDOWS: method_win,
        System.LINUX: method_linux,
        System.DARWIN: method_mac,
    }.get(system)

    # Convert method to list of strings, if it is not already
    if method is None:
        method = get_default_method_names_for_system(system)
    method_names = [method] if isinstance(method, str) else method

    # Convert the method names to module names


def call_function(
    func: KeepAwakeModuleFunction,
    method=None | str | list[str],
    on_method_failure: str | OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
    system: System | None = None,
):
    """Calls one function (e.g. set or unset keepawake) from a specified module

    Parameters
    ----------
    func:
        A KeepAwakeModuleFunction (or a string). Possible values include:
        'set_keepawake', 'unset_keepawake'. This is the name of the function
        in the implementation module to call.

    """

    for method_name in method_names:
        executor = KeepAwakeMethodExecutor(
            system=system,
            method=method_name,
            on_method_failure=on_method_failure,
            on_failure=on_failure,
        )
        result = executor.run(func)


def set_keepawake(
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
    on_method_failure: str | OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    method_win=None | str | list[str] = None,
    method_linux=None | str | list[str] = None,
    method_mac=None | str | list[str] = None,
):
    """
    Parameters
    ----------
    method_win:
        The method or methods to use on Windows. Possible values: 'esflags'
    method_linux:
        The method or methods to use on Linux. Possible values: 'dbus',
        'libdbus', 'systemd'
    method_mac:
        The method or methods to use on MacOS. Possible values: 'caffeinate'
    on_method_failure:
        Tells what to do when a method fails. Makes sense only when there are
        multiple methods used (like on linux; see `method_linux`).
        See also: `on_failure`. Default: 'loginfo'.
    on_failure:
        Tells what to do when setting keepawake fails. This is done when
        *every* (selected) method has failed. See below for the list of
        possible values. Default: 'error'.

    Details
    ---------
    Possible values for `on_failure` and `on_method_failure`:

        'error':  raise wakepy.KeepAwakeError
        'warn': call warnings.warn
        'print': print to stdout
        'logerror': Use python logging with log level = 'error'
        'logwarn': Use python logging with log level = 'warning'
        'loginfo': Use python logging with log level = 'info'
        'logdebug': Use python logging with log level = 'debug'
        'pass': do nothing


    """

    outcome = call_function(
        func=KeepAwakeModuleFunction.SET_KEEPAWAKE,
        method=method,
        on_method_failure=on_method_failure,
        on_failure=on_failure,
        system=CURRENT_SYSTEM,
    )


def unset_keepawake(
    method_win=None | str | list[str],
    method_linux=None | str | list[str],
    method_mac=None | str | list[str],
):
    raise NotImplementedError()


@contextmanager
def keepawake(
    *args,
    method_win=None | str | list[str],
    method_linux=None | str | list[str],
    method_mac=None | str | list[str],
    **kwargs,
):
    set_keepawake(*args, **kwargs)

    try:
        yield
    finally:
        unset_keepawake()
