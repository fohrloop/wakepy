from __future__ import annotations

import typing

from ..core.constants import ModeName
from ..core.mode import create_mode

if typing.TYPE_CHECKING:
    from typing import Optional, Type

    from ..core.activation import MethodsPriorityOrder
    from ..core.dbus import DbusAdapter, DbusAdapterTypeSeq
    from ..core.method import StrCollection
    from ..core.mode import Mode, OnFail


def running(
    methods: Optional[StrCollection] = None,
    omit: Optional[StrCollection] = None,
    methods_priority: Optional[MethodsPriorityOrder] = None,
    on_fail: OnFail = "error",
    dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None,
) -> Mode:
    """Create a wakepy mode (a context manager) for keeping programs running.
    The properties of the keep.running mode are:

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

    Parameters
    ----------
    methods: list, tuple or set of str
        The names of Methods to select from the keep.running mode; a
        "whitelist" filter. Means "use these and only these Methods". Any
        Methods in `methods` but not in the keep.running mode will raise a
        ValueError. Cannot be used same time with `omit`. Optional.
    omit: list, tuple or set of str or None
        The names of Methods to remove from the keep.running mode; a
        "blacklist" filter. Any Method in `omit` but not in the keep.running
        mode will be silently ignored. Cannot be used same time with
        `methods`. Optional.
    methods_priority: list[str | set[str]]
        The priority order for the methods to be used when entering the
        keep.running mode. You may use this parameter to force or suggest the
        order in which Methods are used. Any methods not explicitly supported
        by the current platform will automatically be unused (no need to add
        them here). The format is a list[str | set[str]], where each
        string is a Method name. Any method within a set will have equal
        user-given priority, and they are prioritized with the automatic
        prioritization rules. The first item in the list has the highest
        priority. All method names must be unique and must be part of the
        keep.running Mode.

        The asterisk ('*') can be used to mean "all other methods"
        and may occur only once in the priority order, and cannot be part of a
        set. If asterisk is not part of the `methods_priority`, it will be
        added as the last element automatically.
    on_fail: str | callable
        Determines what to do in case mode activation fails. Valid options are:
        "error", "warn", "pass" and a callable. If the option is "error",
        raises wakepy.ActivationError. Is selected "warn", issues warning. If
        "pass", does nothing. If `on_fail` is a callable, it must take one
        positional argument: result, which is an instance of ActivationResult.
        The ActivationResult contains more detailed information about the
        activation process.
    dbus_adapter: class or sequence of classes 
        Optional argument which can be used to define a custom DBus adapter.
        If given, should be a subclass of :class:`~wakepy.DbusAdapter`, or a
        list of such.

    Returns
    -------
    keep_running_mode: Mode
        The context manager for keeping a system running.

        
    Examples
    --------
    >>> with keep.running() as k:
    >>>     # do something that takes a long time.
    """
    return create_mode(
        modename=ModeName.KEEP_RUNNING,
        omit=omit,
        methods=methods,
        methods_priority=methods_priority,
        on_fail=on_fail,
        dbus_adapter=dbus_adapter,
    )


def presenting(
    methods: Optional[StrCollection] = None,
    omit: Optional[StrCollection] = None,
    methods_priority: Optional[MethodsPriorityOrder] = None,
    on_fail: OnFail = "error",
    dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None,
) -> Mode:
    """Create a wakepy mode (a context manager) for keeping a system running
    and showing content.


    Parameters
    ----------
    methods: list, tuple or set of str
        The names of Methods to select from the keep.presenting mode; a
        "whitelist" filter. Means "use these and only these Methods". Any
        Methods in `methods` but not in the keep.presenting mode will raise a
        ValueError. Cannot be used same time with `omit`. Optional.
    omit: list, tuple or set of str or None
        The names of Methods to remove from the keep.presenting mode; a
        "blacklist" filter. Any Method in `omit` but not in the keep.presenting
        mode will be silently ignored. Cannot be used same time with
        `methods`. Optional.
    methods_priority: list[str | set[str]]
        The priority order for the methods to be used when entering the
        keep.presenting mode. You may use this parameter to force or suggest
        the order in which Methods are used. Any methods not explicitly
        supported by the current platform will automatically be unused (no need
        to add them here). The format is a list[str | set[str]], where each
        string is a Method name. Any method within a set will have equal
        user-given priority, and they are prioritized with the automatic
        prioritization rules. The first item in the list has the highest
        priority. All method names must be unique and must be part of the
        keep.presenting Mode.

        The asterisk ('*') can be used to mean "all other methods"
        and may occur only once in the priority order, and cannot be part of a
        set. If asterisk is not part of the `methods_priority`, it will be
        added as the last element automatically.
    on_fail:
        Determines what to do in case mode activation fails. Valid options are:
        "error", "warn", "pass" and a callable. If the option is "error",
        raises wakepy.ActivationError. Is selected "warn", issues warning. If
        "pass", does nothing. If `on_fail` is a callable, it must take one
        positional argument: result, which is an instance of ActivationResult.
        The ActivationResult contains more detailed information about the
        activation process.
    dbus_adapter: class or sequence of classes 
        Optional argument which can be used to define a custom DBus adapter.
        If given, should be a subclass of :class:`~wakepy.DbusAdapter`, or a
        list of such.

    Returns
    -------
    keep_presenting_mode: Mode
        The context manager for keeping a system presenting content.

    Example
    -------
    >>> with keep.presenting() as k:
    >>>     # do something that takes a long time.

    """
    return create_mode(
        modename=ModeName.KEEP_PRESENTING,
        methods=methods,
        omit=omit,
        methods_priority=methods_priority,
        on_fail=on_fail,
        dbus_adapter=dbus_adapter,
    )
