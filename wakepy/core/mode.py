from __future__ import annotations

import typing
from abc import ABC

from .activation import ActivationResult, activate_one_of_multiple, deactivate_method
from .calls import CallProcessor
from .heartbeat import Heartbeat
from .method import get_methods_for_mode, select_methods

if typing.TYPE_CHECKING:
    from types import TracebackType
    from typing import Optional, Type

    from .activation import MethodsPriorityOrder
    from .constants import ModeName
    from .dbus import DbusAdapter, DbusAdapterTypeSeq
    from .method import Method, StrCollection


class ModeExit(Exception):
    """This can be used to exit from any wakepy mode with block. Just raise it
    within any with block which is a wakepy mode, and no code below it will
    be executed.

    Example
    -------
    ```
    with keep.running():
        # do something
        if some_condition:
            print('failure')
            raise ModeExit
        print('success')
    ```

    This will print just "failure" in case entering a Mode did not succeed and
    just "success" in case it did succeed (never both).
    """


class ModeController:
    def __init__(self, call_processor: CallProcessor):
        self.call_processor = call_processor
        self.active_method: Method | None = None
        self.heartbeat: Heartbeat | None = None

    def activate(
        self,
        method_classes: list[Type[Method]],
        methods_priority: Optional[MethodsPriorityOrder] = None,
    ) -> ActivationResult:
        """Activates the mode with one of the methods in the input method
        classes. The methods are used with descending priority; highest
        priority first.
        """
        result, active_method, heartbeat = activate_one_of_multiple(
            methods=method_classes,
            methods_priority=methods_priority,
            call_processor=self.call_processor,
        )
        self.active_method = active_method
        self.heartbeat = heartbeat
        return result

    def deactivate(self) -> bool:
        """Deactivates the active mode, defined by the active Method, if any.
        If there was no active method, does nothing.

        Returns
        -------
        deactivated:
            If there was no active method, returns False (nothing was done).
            If there was an active method, and it was deactivated, returns True

        Raises
        ------
        MethodError (RuntimeError) if there was active method but an error
        occurred when trying to deactivate it."""

        if not self.active_method:
            return False

        deactivate_method(self.active_method, self.heartbeat)
        self.active_method = None
        self.heartbeat = None
        return True


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
    method_classes: list[Type[Method]]
        The list of methods associated for this mode.
    active: bool
        True if the mode is active. Otherwise, False.
    activation_result: ActivationResult | None
        The activation result which tells more about the activation process
        outcome. None if Mode has not yet been activated.
    """

    _call_processor_class: Type[CallProcessor] = CallProcessor
    _controller_class: Type[ModeController] = ModeController

    def __init__(
        self,
        methods: list[Type[Method]],
        methods_priority: Optional[MethodsPriorityOrder] = None,
        dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None,
    ):
        """Initialize a Mode using Methods.

        This is also where the activation process related settings, such as the
        dbus adapter to be used, are defined.

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

        self.methods_classes = methods
        self.methods_priority = methods_priority
        self.controller: ModeController | None = None
        self.activation_result: ActivationResult | None = None
        self.active: bool = False
        self._dbus_adapter_cls = dbus_adapter

    def __enter__(self) -> Mode:
        if self.controller is None:
            call_processor = self._call_processor_class(
                dbus_adapter=self._dbus_adapter_cls
            )
            self.controller = self._controller_class(call_processor=call_processor)
        self.activation_result = self.controller.activate(
            self.methods_classes,
            methods_priority=self.methods_priority,
        )
        self.active = self.activation_result.success
        return self

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

        if self.controller is None:
            raise RuntimeError("Must __enter__ before __exit__!")

        self.controller.deactivate()
        self.active = False

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
