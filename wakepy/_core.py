"""This module provides the following core functions of wakepy:

keepawake()
    A context manager that sets and unsets keepawake.

set_keepawake()
unset_keepawake()
    The lower level functions that can be used in any script to
    set or unset the keepawake.
"""
from contextlib import contextmanager
import enum
import platform

from ._implementations._windows import methods as windows_methods
from ._implementations._linux import methods as linux_methods
from ._implementations._darwin import methods as darwin_methods


class System(str, enum.Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"



CURRENT_SYSTEM = platform.system().lower()
SUPPORTED_SYSTEMS = list(x.value for x in System.__members__.values())


def get_methods_for_current_system() -> list[KeepawakeMethod]:
    return {
        System.WINDOWS: windows_methods,
        System.LINUX: linux_methods,
        System.DARWIN: darwin_methods,
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


def set_keepawake(
    method_win=None | str | list[str],
    method_linux=None | str | list[str],
    method_mac=None | str | list[str],
    on_method_failure: str 
):
    """
    Parameters
    ----------
    method_win: 
        The
    """
    method_names = get_method_names_from_args_for_current_system(
        method_win=method_win,
        method_linux=method_linux,
        method_mac=method_mac,
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
    method


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
