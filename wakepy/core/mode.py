from __future__ import annotations

import typing
from abc import ABC

from .activationmanager import ModeActivationManager
from .activationresult import ActivationResult
from .method import check_methods_priority, get_methods_for_mode, select_methods

if typing.TYPE_CHECKING:
    from types import TracebackType
    from typing import Optional, Type

    from .constants import ModeName
    from .dbus import DbusAdapter, DbusAdapterTypeSeq
    from .method import Method, MethodsPriorityOrder, StrCollection


class ModeExit(Exception):
    """This can be used to exit from any wakepy mode with block. Just raise it
    within any with block which is a wakepy mode, and no code below it will
    be executed.

    Example
    -------
    ```
    with keep.running() as k:
        if not k.success:
            print('failure')
            raise ModeExit
        print('success')
    ```

    This will print just "failure" in case entering a Mode did not succeed and
    just "success" in case it did succeed (never both).
    """


class Mode(ABC):
    """A mode is something that is entered into, kept, and exited from. Modes
    are implemented as context managers, and user code (inside the with
    statement body) runs during the "keeping" the mode. The "keeping" has
    a possibility to run a heartbeat.

    Purpose of Mode:
    * Provide the main API of wakepy for the user
    * Provide __enter__ for fulfilling the context manager protocol
    * Provide __exit__ for fulfilling the context manager protocol
    * Provide easy way to define list of Methods to be used for entering a mode

    Attributes
    ----------
    methods: list[Type[Method]]
        The list of methods associated for this mode.
    manager: ModeActivationManager
        The manager which lives in the main thread and talks to the
        ModeActivator using queues. This is responsible for activating and
        deactivating a mode.
    """

    _manager_class: Type[ModeActivationManager] = ModeActivationManager

    def __init__(
        self,
        methods: list[Type[Method]],
        methods_priority: Optional[MethodsPriorityOrder] = None,
        dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None,
    ):
        """Initialize a Mode using Methods.

        This is also where the ModeActivationManager settings, such as the dbus
        adapter to be used, are defined.

        Parameters
        ----------
        methods:
            The list of Methods to be used for activating this Mode.
        methods_priority: list[str | set[str]]
            The priority order, which is a list of method names or asterisk
            ('*'). The asterisk means "all rest methods" and may occur only
            once in the priority order, and cannot be part of a set. All method
            names must be unique and must be part of the `methods`.
        dbus_adapter:
            For using a custom dbus-adapter. Optional.
        """
        check_methods_priority(methods_priority, methods)

        self.methods = methods
        self.methods_priority = methods_priority
        self.manager: ModeActivationManager = self._manager_class(
            dbus_adapter=dbus_adapter
        )

    def __enter__(self) -> ActivationResult:
        # TODO: pass the methods_priority
        return self.manager.activate(methods=self.methods)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exception: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        """Called when exiting the with block.

        If with block completed normally, called with (None, None, None)
        If with block had an exception, called with (exc_type, exc_value,
        traceback), which is the same as *sys.exc_info

        Will swallow any ModeExit exception. Other exceptions will be
        re-raised.
        """

        # These are not used but are part of context manager protocol.
        #  make linters happy
        _ = exc_type
        _ = traceback

        self.manager.deactivate()

        if exception is None or isinstance(exception, ModeExit):
            return True

        # Other types of exceptions are not handled; ignoring them here and
        # returning False will tell python to re-raise the exception. Can't
        # return None as type-checkers will mark code after with block
        # unreachable

        return False


def create_mode(
    modename: ModeName,
    methods: Optional[StrCollection] = None,
    omit: Optional[StrCollection] = None,
    methods_priority: Optional[MethodsPriorityOrder] = None,
    dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None,
) -> Mode:
    """
    Creates and returns a Mode (a context manager).

    Parameters
    ----------
    methods: list, tuple or set of str
        The names of Methods to select from the mode defined with `modename`;
        a "whitelist" filter. Means "use these and only these Methods". Any
        Methods in `methods` but not in the selected mode will raise a
        ValueError. Cannot be used same time with `omit`. Optional.
    omit: list, tuple or set of str or None
        The names of Methods to remove from the mode defined with `modename`;
        a "blacklist" filter. Any Method in `omit` but not in the selected mode
        will be silently ignored. Cannot be used same time with `methods`.
        Optional.
    methods_priority: list[str | set[str]]
        The methods_priority parameter for Mode. Used to prioritize methods.
    dbus_adapter:
        Optional argument which can be used to define a customer DBus adapter.

    Returns
    -------
    mode: Mode
        The context manager for the selected mode.
    """
    methods_for_mode = get_methods_for_mode(modename)
    selected_methods = select_methods(methods_for_mode, use_only=methods, omit=omit)
    return Mode(
        methods=selected_methods,
        methods_priority=methods_priority,
        dbus_adapter=dbus_adapter,
    )
