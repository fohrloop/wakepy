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


from ._methods import OnFailureStrategyName, CURRENT_SYSTEM, KeepAwakeMethodExecutor


def set_keepawake(
    method_win=None | str | list[str],
    method_linux=None | str | list[str],
    method_mac=None | str | list[str],
    on_method_failure: str | OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
    on_failure: str | OnFailureStrategyName = OnFailureStrategyName.ERROR,
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
        The method or methods to use on Windows. Possible values: 'caffeinate'

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
    excecutor = KeepAwakeMethodExecutor(
        method_win=method_win,
        method_linux=method_linux,
        method_mac=method_mac,
        on_method_failure=on_method_failure,
        on_failure=on_failure,
    )

    for method_name in method_names:
        call_method(CURRENT_SYSTEM, method_name)

    raise NotImplementedError(
        f"wakepy has not yet a {CURRENT_SYSTEM} implementation. "
        "Pull requests welcome: https://github.com/np-8/wakepy"
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
