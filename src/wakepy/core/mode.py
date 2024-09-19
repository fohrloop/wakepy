"""This module defines the Mode class and functions which may be used in the
activation and deactivation of Modes (using Methods).

Classes
-------
Mode:
    The main class of wakepy. Provides the entry point to any wakepy mode. A
    context manager, which enters the mode defined with one of the Methods
    given to it upon initialization.
"""

from __future__ import annotations

import logging
import os
import typing
import warnings

from wakepy.core.constants import FALSY_ENV_VAR_VALUES, WAKEPY_FAKE_SUCCESS

from .activationresult import ActivationResult, MethodActivationResult
from .dbus import DBusAdapter, get_dbus_adapter
from .heartbeat import Heartbeat
from .method import Method, activate_method, deactivate_method
from .prioritization import order_methods_by_priority
from .registry import get_method, get_methods_for_mode

if typing.TYPE_CHECKING:
    import sys
    from types import TracebackType
    from typing import Callable, List, Optional, Tuple, Type, Union

    from .constants import Collection, ModeName, StrCollection
    from .dbus import DBusAdapter, DBusAdapterTypeSeq
    from .method import Method, MethodCls
    from .prioritization import MethodsPriorityOrder

    if sys.version_info < (3, 8):  # pragma: no-cover-if-py-gte-38
        from typing_extensions import Literal
    else:  # pragma: no-cover-if-py-lt-38
        from typing import Literal

    OnFail = Union[Literal["error", "warn", "pass"], Callable[[ActivationResult], None]]

    MethodClsCollection = Collection[MethodCls]


logger = logging.getLogger(__name__)


class ActivationError(RuntimeError):
    """Raised if the activation of a :class:`Mode` is not successful and the
    on-fail action is to raise an Exception. See the ``on_fail`` parameter of
    the ``Mode`` constructor. This is a subclass of `RuntimeError <https://\
    docs.python.org/3/library/exceptions.html#RuntimeError>`_.
    """


class ActivationWarning(UserWarning):
    """Issued if the activation of a :class:`Mode` is not successful and the
    on-fail action is to issue a Warning. See the ``on_fail`` parameter of
    the ``Mode`` constructor. This is a subclass of `UserWarning <https://docs\
    .python.org/3/library/exceptions.html#UserWarning>`_.
    """


class ModeExit(Exception):
    """This can be used to exit from any wakepy mode with block. Just raise it
    within any with block which is a wakepy mode, and no code below it will
    be executed.

    Examples
    --------
    You may use ``ModeExit`` to exit a with block, like this::

        with keep.running():

            # do something

            if SOME_CONDITION:
                print('failure')
                raise ModeExit
            print('success')

    This will print just "failure" if ``SOME_CONDITION`` is truthy, and
    just "success" in case it did succeed (never both).
    """


class Mode:
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
        "error", raises :class:`~wakepy.ActivationError`. Is selected "warn",
        issues a warning. If "pass", does nothing. If ``on_fail`` is a
        callable, it must take one positional argument: result, which is an
        instance of :class:`ActivationResult`. The ActivationResult contains
        more detailed information about the activation process.
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
    """True if the mode is active. Otherwise, False. See also:
    :attr:`active_method`.
    """

    activation_result: ActivationResult
    """The activation result which tells more about the activation process
    outcome. See :class:`ActivationResult`.
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

    def __init__(
        self,
        method_classes: list[Type[Method]],
        methods_priority: Optional[MethodsPriorityOrder] = None,
        name: Optional[ModeName | str] = None,
        on_fail: OnFail = "warn",
        dbus_adapter: Type[DBusAdapter] | DBusAdapterTypeSeq | None = None,
    ):
        r"""Initialize a `Mode` using `Method`\ s.

        This is also where the activation process related settings, such as the
        dbus adapter to be used, are defined.
        """
        self.method_classes = method_classes
        self.active: bool = False
        self.activation_result = ActivationResult()
        self.name = name
        self.methods_priority = methods_priority
        self.on_fail = on_fail
        self._active_method: Method | None = None
        """This holds the active method instance"""
        self._used_method: Method | None = None
        """This holds the used method instance. The used method instance will
        not be set to None when deactivating."""

        self.heartbeat: Heartbeat | None = None

        self._dbus_adapter_cls = dbus_adapter
        # Retrieved and updated using the _dbus_adapter property
        self._dbus_adapter_instance: DBusAdapter | None = None
        self._dbus_adapter_created: bool = False

        self._logger = logging.getLogger(__name__)

    @classmethod
    def from_name(
        cls,
        mode_name: ModeName,
        methods: Optional[StrCollection] = None,
        omit: Optional[StrCollection] = None,
        methods_priority: Optional[MethodsPriorityOrder] = None,
        on_fail: OnFail = "warn",
        dbus_adapter: Type[DBusAdapter] | DBusAdapterTypeSeq | None = None,
    ) -> Mode:
        """
        Creates and returns a Mode based on a mode name.

        Parameters
        ----------
        mode_name: str
            The name of the mode to create. Must be an existing Mode name;
            something that has used as Method.name attribute in a
            :class:`~wakepy.core.method.Method` subclass. Examples:
            "keep.running", "keep.presenting".
        methods: list, tuple or set of str
            The names of Methods to select from the mode defined with
            `mode_name`; a "whitelist" filter. Means "use these and only these
            Methods". Any Methods in `methods` but not in the selected mode
            will raise a ValueError. Cannot be used same time with `omit`.
            Optional.
        omit: list, tuple or set of str or None
            The names of Methods to remove from the mode defined with
            `mode_name`; a "blacklist" filter. Any Method in `omit` but not in
            the selected mode will be silently ignored. Cannot be used same
            time with `methods`. Optional.
        on_fail: "error" | "warn" | "pass" | Callable
            Determines what to do in case mode activation fails. Valid options
            are: "error", "warn", "pass" and a callable. If the option is
            "error", raises :class:`ActivationError`. Is selected "warn",
            issues a warning. If "pass", does nothing. If ``on_fail`` is a
            callable, it must take one positional argument: result, which is an
            instance of :class:`ActivationResult`. The ActivationResult
            contains more detailed information about the activation process.
        methods_priority: list[str | set[str]]
            The priority order, which is a list of method names or asterisk
            ('*'). The asterisk means "all rest methods" and may occur only
            once in the priority order, and cannot be part of a set. All method
            names must be unique and must be part of the `methods`.
        dbus_adapter:
            For using a custom dbus-adapter. Optional. If not given, the
            default dbus adapter is used, which is :class:`~wakepy.\\
            dbus_adapters.jeepney.JeepneyDBusAdapter`.


        Returns
        -------
        mode: Mode
            The context manager for the selected mode.

        """
        methods_for_mode = get_methods_for_mode(mode_name)
        selected_methods = select_methods(methods_for_mode, use_only=methods, omit=omit)
        return cls(
            name=mode_name,
            method_classes=selected_methods,
            methods_priority=methods_priority,
            on_fail=on_fail,
            dbus_adapter=dbus_adapter,
        )

    def __enter__(self) -> Mode:
        """Called automatically when entering a with block and a instance of
        Mode is used as the context expression. This tries to activate the
        Mode using :attr:`~wakepy.Mode.method_classes`.
        """
        self._activate()
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

        self._deactivate()

        if exception is None or isinstance(exception, ModeExit):
            # Returning True means that the exception within the with block is
            # swallowed. We skip only ModeExit which should simply exit the
            # with block.
            return True

        # Other types of exceptions are not handled; ignoring them here and
        # returning False will tell python to re-raise the exception. Can't
        # return None as type-checkers would mark code after with block
        # unreachable.

        return False

    def _activate(self) -> ActivationResult:
        """Activates the mode with one of the methods which belong to the mode.
        The methods are used with descending priority; highest priority first,
        and the priority is determined with the mode.methods_priority.

        The activation may be faked as to be successful by using the
        WAKEPY_FAKE_SUCCESS environment variable.
        """

        method_classes = add_fake_success_if_required(
            self.method_classes, os.environ.get(WAKEPY_FAKE_SUCCESS)
        )
        method_classes_ordered = order_methods_by_priority(
            method_classes, self.methods_priority
        )

        methodresults, self._active_method, self.heartbeat = (
            self._activate_one_of_methods(
                method_classes=method_classes_ordered,
                dbus_adapter=self._dbus_adapter,
            )
        )

        self.activation_result = ActivationResult(methodresults, mode_name=self.name)
        self.active = self.activation_result.success
        self._used_method = self._active_method

        if not self.active:
            handle_activation_fail(self.on_fail, self.activation_result)

        return self.activation_result

    @staticmethod
    def _activate_one_of_methods(
        method_classes: list[Type[Method]], **method_kwargs: object
    ) -> Tuple[List[MethodActivationResult], Optional[Method], Optional[Heartbeat]]:
        """Activates mode using the first Method in `method_classes` which
        succeeds. The methods are tried in the order given in `method_classes`
        argument.

        Parameters
        ----------
        method_classes:
            The list of Methods to be used for activating this Mode.
        method_kwargs:
            optional kwargs passed to the all the Method class constructors.

        Returns
        -------
        List[MethodActivationResult], Optional[Method], Optional[Heartbeat]
            A three-tuple: The list of method activation results, the activated
            method (None if not any), the activated heartbeat (None if not
            any).
        """

        methodresults = []
        while method_classes:
            methodcls = method_classes.pop(0)
            method = methodcls(**method_kwargs)
            methodresult, heartbeat = activate_method(method)
            methodresults.append(methodresult)
            if methodresult.success:
                break
        else:
            # Tried activate with all methods, but none of them succeed
            method, heartbeat = None, None

        # Add unused methods to the results
        for method_cls in method_classes:
            methodresults.append(
                MethodActivationResult(
                    method_cls.name, mode_name=method_cls.mode_name, success=None
                )
            )

        return methodresults, method, heartbeat

    def _deactivate(self) -> bool:
        """Deactivates the active mode, defined by the active Method, if any.
        If there was no active method, does nothing.

        Returns
        -------
        deactivated:
            If there was no active method, returns False (nothing was done).
            If there was an active method, and it was deactivated, returns True

        Raises
        ------
        RuntimeError, if there was active method but an error occurred when
        trying to deactivate it."""

        if self.active:
            if self._active_method is None:
                raise RuntimeError(
                    f"Cannot deactivate mode: {str(self.name)}. The active_method is None! This should never happen."  # noqa E501
                )
            deactivate_method(self._active_method, self.heartbeat)
            deactivated = True
        else:
            deactivated = False

        self._active_method = None
        self.heartbeat = None
        self.active = False

        return deactivated

    @property
    def _dbus_adapter(self) -> DBusAdapter | None:
        """The DbusAdapter instance of the Mode, if any. Created on the first
        call."""
        if not self._dbus_adapter_created:
            # Only do this once even if the returned instance is None, as this
            # might be a costly operation.
            self._dbus_adapter_instance = get_dbus_adapter(self._dbus_adapter_cls)
            self._dbus_adapter_created = True
        return self._dbus_adapter_instance

    @property
    def active_method(self) -> str | None:
        """The name of the active Method. None if Mode is not active. See also
        :attr:`used_method`."""
        if self._active_method is None:
            return None
        return self._active_method.name

    @property
    def used_method(self) -> str | None:
        """The name of the currently used (active) or previously used (already
        deactivated) Method. None If Mode has never been activated. See also:
        :attr:`active_method`."""
        if self._used_method is None:
            return None
        return self._used_method.name


def select_methods(
    methods: MethodClsCollection,
    omit: Optional[StrCollection] = None,
    use_only: Optional[StrCollection] = None,
) -> List[MethodCls]:
    """Selects Methods from from `methods` using a blacklist (omit) or
    whitelist (use_only). If `omit` and `use_only` are both None, will return
    all the original methods.

    Parameters
    ----------
    methods: collection of Method classes
        The collection of methods from which to make the selection.
    omit: list, tuple or set of str or None
        The names of Methods to remove from the `methods`; a "blacklist"
        filter. Any Method in `omit` but not in `methods` will be silently
        ignored. Cannot be used same time with `use_only`. Optional.
    use_only: list, tuple or set of str
        The names of Methods to select from the `methods`; a "whitelist"
        filter. Means "use these and only these Methods". Any Methods in
        `use_only` but not in `methods` will raise a ValueErrosr. Cannot
        be used same time with `omit`. Optional.

    Returns
    -------
    methods: list[MethodCls]
        The selected method classes.

    Raises
    ------
    ValueError if the input arguments (omit or use_only) are invalid.
    """

    if omit and use_only:
        raise ValueError(
            "Can only define omit (blacklist) or use_only (whitelist), not both!"
        )
    elif omit is None and use_only is None:
        selected_methods = list(methods)
    elif omit is not None:
        selected_methods = [m for m in methods if m.name not in omit]
    elif use_only is not None:
        selected_methods = [m for m in methods if m.name in use_only]
        if not set(use_only).issubset(m.name for m in selected_methods):
            missing = sorted(set(use_only) - set(m.name for m in selected_methods))
            raise ValueError(
                f"Methods {missing} in `use_only` are not part of `methods`!"
            )
    else:  # pragma: no cover
        raise ValueError("Invalid `omit` and/or `use_only`!")

    return selected_methods


def add_fake_success_if_required(
    method_classes: List[Type[Method]], wakepy_fake_success: str | None
) -> List[Type[Method]]:
    """Adds the WAKEPY_FAKE_SUCCESS method to the list of method classes, if
    the WAKEPY_FAKE_SUCCESS environment variable has been set into a non-falsy
    value. See also: `should_fake_success`.

    Parameters
    ----------
    method_classes:
        The list of method classes
    wakepy_fake_success:
        Value read from WAKEPY_FAKE_SUCCESS environment variable; either None
        or a string. For example: '0', '1', 'True', or 'False'. None has same
        behavior as falsy values ('0', 'no', 'false', 'f', 'n', '').
    """
    if not should_fake_success(wakepy_fake_success):
        return method_classes

    return [get_method(WAKEPY_FAKE_SUCCESS)] + method_classes


def should_fake_success(wakepy_fake_success: str | None) -> bool:
    """Function which says if fake success should be enabled

    Parameters
    ----------
    wakepy_fake_success:
        Value read from WAKEPY_FAKE_SUCCESS environment variable; either None
        or a string. For example: '0', '1', 'True', or 'False'. None has same
        behavior as falsy values ('0', 'no', 'false', 'f', 'n', '').

    Returns
    -------
    fake_success_enabled:
        True, if fake success is enabled, False otherwise.

    Motivation
    ----------
    When running on CI system, wakepy might fail to acquire an inhibitor
    lock just because there is no Desktop Environment running. In these
    cases, it might be useful to just tell with an environment variable
    that wakepy should fake the successful inhibition anyway. Faking the
    success is done after every other method is tried (and failed).
    """

    if wakepy_fake_success is None:
        logger.debug("'%s' not set.", WAKEPY_FAKE_SUCCESS)
        return False

    if wakepy_fake_success.lower() in FALSY_ENV_VAR_VALUES:
        logger.info(
            "'%s' set to a falsy value: %s.", WAKEPY_FAKE_SUCCESS, wakepy_fake_success
        )
        return False

    logger.info(
        "'%s' set to a truthy value: %s.", WAKEPY_FAKE_SUCCESS, wakepy_fake_success
    )
    return True


def handle_activation_fail(on_fail: OnFail, result: ActivationResult) -> None:
    if on_fail == "pass":
        return
    elif on_fail == "warn":
        warnings.warn(result.get_failure_text(), ActivationWarning)
        return
    elif on_fail == "error":
        raise ActivationError(result.get_failure_text())
    elif not callable(on_fail):
        raise ValueError(
            'on_fail must be one of "error", "warn", pass" or a callable which takes '
            "single positional argument (ActivationResult)"
        )
    on_fail(result)
