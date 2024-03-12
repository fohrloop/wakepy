from __future__ import annotations

import typing
import warnings
from abc import ABC

from .activation import ActivationResult, activate_mode, deactivate_method
from .dbus import get_dbus_adapter
from .heartbeat import Heartbeat
from .method import select_methods
from .registry import get_methods_for_mode

if typing.TYPE_CHECKING:
    from types import TracebackType
    from typing import Callable, Literal, Optional, Type

    from .activation import MethodsPriorityOrder
    from .constants import ModeName
    from .dbus import DBusAdapter, DBusAdapterTypeSeq
    from .method import Method, StrCollection

    OnFail = Literal["error", "warn", "pass"] | Callable[[ActivationResult], None]


class ActivationError(RuntimeError):
    """Raised if activation is not successful and on-fail action is to raise
    Exception."""


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
    def __init__(self, dbus_adapter: Optional[DBusAdapter] = None):
        self.dbus_adapter = dbus_adapter
        self.active_method: Method | None = None
        self.heartbeat: Heartbeat | None = None

    def activate(
        self,
        method_classes: list[Type[Method]],
        methods_priority: Optional[MethodsPriorityOrder] = None,
        modename: Optional[str] = None,
    ) -> ActivationResult:
        """Activates the mode with one of the methods in the input method
        classes. The methods are used with descending priority; highest
        priority first.
        """
        result, active_method, heartbeat = activate_mode(
            methods=method_classes,
            methods_priority=methods_priority,
            dbus_adapter=self.dbus_adapter,
            modename=modename,
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
    """A mode is something that is activated (entered in) and deactivated
    (exited from). Each Mode instance is created with a set of Method classes,
    and each one of the Methods may be used to activate the Mode. There are
    multiple Methods for each Mode as there are multiple different operating
    systems, platforms and desktop environments which might need different
    activation strategy, but for a single system only one Method would be
    enough for Mode activation. The rest are typically just for supporting
    other platforms/DEs/etc.

    Modes are implemented as context managers, and user code runs when the mode
    is active. When the mode is active, there is a possibility to run a
    heartbeat (implemented in a future version).

    **Purpose of Mode**:

    * Provide the main API of wakepy for the user
    * Provide `__enter__` and `__exit__`  for fulfilling the `context manager
      protocol <https://peps.python.org/pep-0343/>`_
    * Provide easy way to define list of Methods to be used for entering a mode

    Modes are usually created with a factory function like
    :func:`keep.presenting <wakepy.keep.presenting>` or  :func:`keep.running
    <wakepy.keep.running>`, but using the :class:`~wakepy.Mode` separately
    can be used for more fine-grained control.

    Parameters
    ----------
    methods:
        The list of Methods to be used for activating this Mode.
    methods_priority: list[str | set[str]]
        The priority order, which is a list of method names or asterisk
        ('*'). The asterisk means "all rest methods" and may occur only
        once in the priority order, and cannot be part of a set. All method
        names must be unique and must be part of the `methods`.
    name:
        Name of the Mode. Used for communication to user, logging and in
        error messages (can be "any string" which makes sense to you).
        Optional.
    on_fail: "error" | "warn" | "pass" | Callable
        Determines what to do in case mode activation fails. Valid options
        are: "error", "warn", "pass" and a callable. If the option is
        "error", raises wakepy.ActivationError. Is selected "warn", issues
        warning. If "pass", does nothing. If `on_fail` is a callable, it
        must take one positional argument: result, which is an instance of
        ActivationResult. The ActivationResult contains more detailed
        information about the activation process.
    dbus_adapter:
        For using a custom dbus-adapter. Optional. If not given, the
        default dbus adapter is used, which is :class:`~wakepy.dbus_adapters.\\
        jeepney.JeepneyDBusAdapter`
    """

    method_classes: list[Type[Method]]
    """The list of methods associated for this mode as given when creating the
    ``Mode``. For details, see the documentation of  ``methods`` in the
    :class:`Mode` constructor parameters.
    """

    active: bool
    """True if the mode is active. Otherwise, False.
    """

    activation_result: ActivationResult | None
    """The activation result which tells more about the activation process
    outcome. None if Mode has not yet been activated.
    """

    name: str | None
    """The ``name`` given when creating the :class:`Mode`.
    """

    methods_priority: Optional[MethodsPriorityOrder]
    """The ``methods_priority`` given when creating the :class:`Mode`.
    """

    on_fail: OnFail
    """The ``on_fail`` given when creating the :class:`Mode`.
    """

    dbus_adapter: DBusAdapter | None
    r"""The DBus adapter used with ``Method``\ s which require DBus (if any).
    """

    _controller_class: Type[ModeController] = ModeController

    def __init__(
        self,
        methods: list[Type[Method]],
        methods_priority: Optional[MethodsPriorityOrder] = None,
        name: Optional[ModeName | str] = None,
        on_fail: OnFail = "error",
        dbus_adapter: Type[DBusAdapter] | DBusAdapterTypeSeq | None = None,
    ):
        r"""Initialize a `Mode` using `Method`\ s.

        This is also where the activation process related settings, such as the
        dbus adapter to be used, are defined.
        """

        self.name = name
        self.method_classes = methods
        self.methods_priority = methods_priority
        self.controller: ModeController | None = None
        self.activation_result: ActivationResult | None = None
        self.active: bool = False
        self.on_fail = on_fail
        self._dbus_adapter_cls = dbus_adapter

    def __enter__(self) -> Mode:
        """Called automatically when entering a with block and a instance of
        Mode is used as the context expression. This tries to activate the
        Mode using :attr:`~wakepy.Mode.method_classes`.
        """

        self.controller = self.controller or self._controller_class(
            dbus_adapter=get_dbus_adapter(self._dbus_adapter_cls)
        )
        self.activation_result = self.controller.activate(
            self.method_classes,
            methods_priority=self.methods_priority,
            modename=self.name,
        )
        self.active = self.activation_result.success

        if not self.active:
            handle_activation_fail(self.on_fail, self.activation_result)

        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exception: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        """Called when exiting the with block.

        If with block completed normally, called with `(None, None, None)`
        If with block had an exception, called with `(exc_type, exc_value,
        traceback)`, which is the same as `*sys.exc_info`.

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
            # Returning True means that the exception within the with block is
            # swallowed. We skip only ModeExit which should simply exit the
            # with block.
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
    **kwargs,
) -> Mode:
    """
    Creates and returns a Mode (a context manager).

    Parameters
    ----------
    modename:
        The name of the mode to create. Used for debugging, logging, warning
        and error messaged. Could be basically any string.
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
    **kwargs
        Passed to Mode as initialization arguments.


    Returns
    -------
    mode: Mode
        The context manager for the selected mode.
    """
    methods_for_mode = get_methods_for_mode(modename)
    selected_methods = select_methods(methods_for_mode, use_only=methods, omit=omit)
    return Mode(name=modename, methods=selected_methods, **kwargs)


def handle_activation_fail(on_fail: OnFail, result: ActivationResult):
    if on_fail == "pass":
        return
    elif on_fail == "warn" or on_fail == "error":
        if on_fail == "warn":
            warnings.warn(result.get_error_text())
            return
        else:
            raise ActivationError(result.get_error_text())
    elif not callable(on_fail):
        raise ValueError(
            'on_fail must be one of "error", "warn", pass" or a callable which takes '
            "single positional argument (ActivationResult)"
        )
    on_fail(result)
