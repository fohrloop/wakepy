from __future__ import annotations

import typing

from ..core.mode import Mode
from ..methods.gnome import GnomeSessionManagerNoIdle, GnomeSessionManagerNoSuspend

if typing.TYPE_CHECKING:
    from typing import List, Type

    from ..core.dbus import DbusAdapter, DbusAdapterTypeSeq
    from ..core.method import Method


running_methods: List[Type[Method]] = [
    GnomeSessionManagerNoSuspend,
]
presenting_methods: List[Type[Method]] = [
    GnomeSessionManagerNoIdle,
]


def running(dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None) -> Mode:
    """A wakepy mode and context manager for keeping programs running.

    Properties
    ----------
    1) The system may not go to sleep meaning that programs will continue
       running and can use CPU.
    2) Does prevent only the automatical, idle timer timeout based sleep /
       suspend; Will not prevent user manually entering sleep from a menu, by
       closing a laptop lid or by pressing a power button, for example.
    3) System may still automatically log out user, enable lockscreen
       or turn off the display.
    4) If the process holding the lock dies, the lock is automatically removed.
       There are no methods in keep.running mode which for example would
       perform system-wide configuration changes or anything which would need
       manual reversal.

    Usage
    -----

    ```
    with keep.running() as k:
        if k.failed:
            # fall back or notify user

        # do something that takes a long time.
    ```

    Parameters
    ----------
    dbus_adapter:
        Optional argument which can be used to define a customer DBus adapter.

    Returns
    -------
    keep_running_mode: Mode
        The context manager for keeping a system running.

    """
    return Mode(methods=running_methods, dbus_adapter=dbus_adapter)


def presenting(
    dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None,
) -> Mode:
    """The keep.presenting mode context manager.

    Usage:

    ```
    with keep.presenting() as k:
        if k.failed:
            # fall back or notify user

        # do something that takes a long time.
    ```

    Parameters
    ----------
    dbus_adapter:
        Optional argument which can be used to define a customer DBus adapter.

    Returns
    -------
    keep_presenting_mode: Mode
        The context manager for keeping a system presenting content.
    """
    return Mode(methods=presenting_methods, dbus_adapter=dbus_adapter)
