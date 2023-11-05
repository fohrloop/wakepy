from __future__ import annotations

import typing

from ..core.mode import Mode
from ..methods.gnome import GnomeSessionManagerNoIdle, GnomeSessionManagerNoSuspend

if typing.TYPE_CHECKING:
    from typing import Type, List

    from ..core.method import Method
    from ..core.dbus import DbusAdapter, DbusAdapterTypeSeq


running_methods: List[Method] = [
    GnomeSessionManagerNoSuspend,
]
presenting_methods: List[Method] = [
    GnomeSessionManagerNoIdle,
]


def running(dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None):
    """The keep.running mode context manager.

    Usage:

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
    """
    return Mode(methods=running_methods, dbus_adapter=dbus_adapter)


def presenting(dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None):
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
    """
    return Mode(methods=presenting_methods, dbus_adapter=dbus_adapter)
