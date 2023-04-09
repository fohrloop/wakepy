"""This module provides the following core functions of wakepy:

keepawake()
    A context manager that sets and unsets keepawake.

set_keepawake()
unset_keepawake()
    The lower level functions that can be used in any script to
    set or unset the keepawake.
"""

from __future__ import annotations

from contextlib import contextmanager


from ._methods import (
    KeepAwakeMethodExecutor,
    OnFailureStrategyName,
    SystemName,
    CURRENT_SYSTEM,
    get_default_method_names_for_system,
)


from .constants import KeepAwakeModuleFunctionName


def method_arguments_to_list_of_methods(
    method_win=None | str | list[str],
    method_linux=None | str | list[str],
    method_mac=None | str | list[str],
    system: SystemName | None = None,
) -> list[str]:
    """Based on the input arguments, return the list of method names for the
    system. If the input of methods for the system is None, return the list
    of default methods. By default, use current system as `system`.

    Returns
    -------
    methods:
        List of strings, corresponding to the method names.
    """

    system = system or CURRENT_SYSTEM

    # Select the input argument based on system
    methods = {
        SystemName.WINDOWS: method_win,
        SystemName.LINUX: method_linux,
        SystemName.DARWIN: method_mac,
    }.get(system)

    # Convert method to list of strings, if it is not already
    methods = [methods] if isinstance(methods, str) else methods
    methods = methods or get_default_method_names_for_system(system)
    return methods


def call_a_keepawake_function(
    func: KeepAwakeModuleFunctionName,
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
    on_method_failure: str | OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    methods: None | list[str] = None,
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

    for method in methods:
        executor = KeepAwakeMethodExecutor(
            system=system,
            method=method,
            on_method_failure=on_method_failure,
            on_failure=on_failure,
        )
        result = executor.run(func)


def set_keepawake(
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
    on_method_failure: str | OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    method_win: None | str | list[str] = None,
    method_linux: None | str | list[str] = None,
    method_mac: None | str | list[str] = None,
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

    methods = method_arguments_to_list_of_methods(
        method_win=method_win,
        method_linux=method_linux,
        method_mac=method_mac,
        system=CURRENT_SYSTEM,
    )

    outcome = call_a_keepawake_function(
        func=KeepAwakeModuleFunctionName.SET_KEEPAWAKE,
        on_failure=on_failure,
        on_method_failure=on_method_failure,
        methods=methods,
        system=CURRENT_SYSTEM,
    )


def unset_keepawake(
    method_win: None | str | list[str],
    method_linux: None | str | list[str],
    method_mac: None | str | list[str],
):
    raise NotImplementedError()


@contextmanager
def keepawake(
    *args,
    method_win: None | str | list[str],
    method_linux: None | str | list[str],
    method_mac: None | str | list[str],
    **kwargs,
):
    set_keepawake(*args, **kwargs)

    try:
        yield
    finally:
        unset_keepawake()
