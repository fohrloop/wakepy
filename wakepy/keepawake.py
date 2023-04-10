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


from .constants import KeepAwakeModuleFunctionName, SystemName, OnFailureStrategyName
from ._core import call_a_keepawake_function_with_methods, CURRENT_SYSTEM


def method_arguments_to_list_of_methods_or_none(
    method_win=None | str | list[str],
    method_linux=None | str | list[str],
    method_mac=None | str | list[str],
    system: SystemName | None = None,
) -> list[str] | None:
    """Based on the input arguments, return the correct input arguments for the
    system. Convert string inputs to list of strings. By default, use current
    system as `system`.

    Returns
    -------
    methods:
        List of strings, corresponding to the method names, or None.
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

    return methods


def set_keepawake(
    keep_screen_awake: bool = False,
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
    on_method_failure: str | OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    method_win: None | str | list[str] = None,
    method_linux: None | str | list[str] = None,
    method_mac: None | str | list[str] = None,
):
    """
    Parameters
    ----------
    keep_screen_awake: bool
        If True, keeps also the screen awake, if implemented on system.
        * windows: works (default: False)
        * linux: always True and cannot be changed.
        * mac: ? (untested)
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

    methods = method_arguments_to_list_of_methods_or_none(
        method_win=method_win,
        method_linux=method_linux,
        method_mac=method_mac,
        system=CURRENT_SYSTEM,
    )

    return call_a_keepawake_function_with_methods(
        func=KeepAwakeModuleFunctionName.SET_KEEPAWAKE,
        on_failure=on_failure,
        on_method_failure=on_method_failure,
        methods=methods,
        system=CURRENT_SYSTEM,
        keep_screen_awake=keep_screen_awake,
    )


def unset_keepawake(
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

    methods = method_arguments_to_list_of_methods_or_none(
        method_win=method_win,
        method_linux=method_linux,
        method_mac=method_mac,
        system=CURRENT_SYSTEM,
    )

    return call_a_keepawake_function_with_methods(
        func=KeepAwakeModuleFunctionName.UNSET_KEEPAWAKE,
        on_failure=on_failure,
        on_method_failure=on_method_failure,
        methods=methods,
        system=CURRENT_SYSTEM,
    )


@contextmanager
def keepawake(
    keep_screen_awake: bool = False,
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
    on_method_failure: str | OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    method_win: None | str | list[str] = None,
    method_linux: None | str | list[str] = None,
    method_mac: None | str | list[str] = None,
):
    """Keep system awake (not susped/sleep). This is the recommended over
    set_keepawake and unset_keepawake the same (first succesful) method of
    set_keepawake should be used also on unset_keepawake.

    Usage Example
    -------------

    KEEPAWAKE_OPTS = dict(
        keep_screen_awake=True,
        on_failure = 'error',
        on_method_failure = 'logwarn',
        method_linux = ['dbus', 'libdbus', 'systemd'],
    )

    with keepawake(**KEEPAWAKE_OPTS):
        # do stuff that takes a long time.

    Parameters
    ----------
    keep_screen_awake: bool
        If True, keeps also the screen awake, if implemented on system.
        * windows: works (default: False)
        * linux: always True and cannot be changed.
        * mac: ? (untested)
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
    res = set_keepawake(
        keep_screen_awake=keep_screen_awake,
        on_failure=on_failure,
        on_method_failure=on_method_failure,
        method_win=method_win,
        method_linux=method_linux,
        method_mac=method_mac,
    )

    try:
        yield
    finally:
        # This is the same as calling unset_keepawake
        # but forcing the method. It only makes sense to use the
        # unset_keepawake with the same method as which was used
        # to set the keepawake.
        return call_a_keepawake_function_with_methods(
            func=KeepAwakeModuleFunctionName.UNSET_KEEPAWAKE,
            on_failure=on_failure,
            on_method_failure=on_method_failure,
            methods=[res.method_used],
            system=CURRENT_SYSTEM,
        )
