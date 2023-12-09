from __future__ import annotations

import typing

from ..core.constants import ModeName
from ..core.mode import create_mode
from ..methods.gnome import GnomeSessionManagerNoIdle, GnomeSessionManagerNoSuspend

if typing.TYPE_CHECKING:
    from typing import List, Optional, Type

    from ..core.dbus import DbusAdapter, DbusAdapterTypeSeq
    from ..core.method import Method, StrCollection
    from ..core.mode import Mode

running_methods: List[Type[Method]] = [
    GnomeSessionManagerNoSuspend,
]
presenting_methods: List[Type[Method]] = [
    GnomeSessionManagerNoIdle,
]


def running(
    skip: Optional[StrCollection] = None,
    use_only: Optional[StrCollection] = None,
    dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None,
) -> Mode:
    """Create a wakepy mode (a context manager) for keeping programs running.

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
    skip: list, tuple or set of str or None
        The names of Methods to remove from the keep.running mode; a
        "blacklist" filter. Any Method in `skip` but not in the keep.running
        mode will be silently ignored. Cannot be used same time with
        `use_only`. Optional.
    use_only: list, tuple or set of str
        The names of Methods to select from the keep.running mode; a
        "whitelist" filter. Means "use these and only these Methods". Any
        Methods in `use_only` but not in the keep.running mode will raise a
        ValueError. Cannot be used same time with `skip`. Optional.
    dbus_adapter:
        Optional argument which can be used to define a customer DBus adapter.

    Returns
    -------
    keep_running_mode: Mode
        The context manager for keeping a system running.

    """
    return create_mode(
        modename=ModeName.KEEP_RUNNING,
        skip=skip,
        use_only=use_only,
        dbus_adapter=dbus_adapter,
    )


def presenting(
    skip: Optional[StrCollection] = None,
    use_only: Optional[StrCollection] = None,
    dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None,
) -> Mode:
    """Create a wakepy mode (a context manager) for keeping a system running
    and showing content.

    Usage:

    ```
    with keep.presenting() as k:
        if k.failed:
            # fall back or notify user

        # do something that takes a long time.
    ```

    Parameters
    ----------
    skip: list, tuple or set of str or None
        The names of Methods to remove from the keep.running mode; a
        "blacklist" filter. Any Method in `skip` but not in the keep.running
        mode will be silently ignored. Cannot be used same time with
        `use_only`. Optional.
    use_only: list, tuple or set of str
        The names of Methods to select from the keep.running mode; a
        "whitelist" filter. Means "use these and only these Methods". Any
        Methods in `use_only` but not in the keep.running mode will raise a
        ValueError. Cannot be used same time with `skip`. Optional.
    dbus_adapter:
        Optional argument which can be used to define a customer DBus adapter.


    Returns
    -------
    keep_presenting_mode: Mode
        The context manager for keeping a system presenting content.
    """
    return create_mode(
        modename=ModeName.KEEP_PRESENTING,
        skip=skip,
        use_only=use_only,
        dbus_adapter=dbus_adapter,
    )
