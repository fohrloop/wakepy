"""This package (wakepy._deprecated) holds the following deprecated functions

- set_keepawake
- unset_keepawake
- keepawake (context manager)

These were deprecated in 0.7.0 in will be removed in a subsequent release.
"""

from __future__ import annotations

from contextlib import contextmanager
from importlib import import_module

from .._system import CURRENT_SYSTEM

def get_function(funcname, system=CURRENT_SYSTEM):
    module =  import_module(f"._{system}", "wakepy._deprecated")
    return module.__getattr__(funcname)

def set_keepawake(
    keep_screen_awake: bool = False,
):
    """Set a wakelock for keeping system awake (disallow susped/sleep). This is
    lower level function, and usage of the :func:`keepawake` context manager is
    recommended for most situations, as to unset the keepawake, same (first
    succesful) method should be used in :func:`unset_keepawake`.

    Parameters
    ----------
    keep_screen_awake: bool
        If True, keeps also the screen awake, if implemented on system.
          * windows: works (default: False)
          * linux: always True and cannot be changed.
          * mac: ? (untested)
    """
    func = get_function('set_keepawake')
    func(keep_screen_awake=keep_screen_awake)


def unset_keepawake():
    """Uset a wakelock (allow susped/sleep again). This is lower level
    function, and usage of the :func:`keepawake` context manager is
    recommended for most situations, as to unset the keepawake, same (first
    succesful) method of :func:`set_keepawake` should be used here.
    """
    func = get_function('unset_keepawake')
    func()

@contextmanager
def keepawake(*args, **kwargs):
    set_keepawake(*args, **kwargs)

    try:
        yield
    finally:
        unset_keepawake()
