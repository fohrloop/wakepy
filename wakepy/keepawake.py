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
    OnFailureStrategyName,
    System,
    CURRENT_SYSTEM,
    SUPPORTED_SYSTEMS,
    get_default_method_names_for_system,
)


def get_method_names_from_args_for_system(
    method_win=None | str | list[str],
    method_linux=None | str | list[str],
    method_mac=None | str | list[str],
    system: System | None = None,
) -> list[str]:
    system = system or CURRENT_SYSTEM

    if system not in SUPPORTED_SYSTEMS:
        return []

    methodnames = {
        System.WINDOWS: method_win,
        System.LINUX: method_linux,
        System.DARWIN: method_mac,
    }.get(system)

    if methodnames is None:
        methodnames = get_default_method_names_for_system(system)
    elif isinstance(methodnames, str):
        methodnames = [methodnames]
    return methodnames


def set_keepawake(
    method_win=None | str | list[str],
    method_linux=None | str | list[str],
    method_mac=None | str | list[str],
    on_method_failure: str | OnFailureStrategyName = OnFailureStrategyName.LOGINFO,
):
    """
    Parameters
    ----------
    method_win:
        The
    """
    method_names = get_method_names_from_args_for_system(
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
