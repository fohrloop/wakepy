from __future__ import annotations

from contextlib import contextmanager
from importlib import import_module

def import_module_for_method(system, method):
    return import_module(f"._{system}._{method}", "wakepy._deprecated")



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
    ... # TODO


def unset_keepawake():
    """Uset a wakelock (allow susped/sleep again). This is lower level
    function, and usage of the :func:`keepawake` context manager is
    recommended for most situations, as to unset the keepawake, same (first
    succesful) method of :func:`set_keepawake` should be used here.
    """
    ... # TODO 

@contextmanager
def keepawake(*args, **kwargs):
    set_keepawake(*args, **kwargs)

    try:
        yield
    finally:
        unset_keepawake()
