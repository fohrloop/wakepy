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
from .method import Method, MethodInfo, activate_method, deactivate_method
from .prioritization import order_methods_by_priority
from .registry import get_method, get_methods_for_mode

if typing.TYPE_CHECKING:
    import sys
    from types import TracebackType
    from typing import Callable, List, Optional, Tuple, Type, Union

    from .constants import Collection, ModeName, StrCollection
    from .dbus import DBusAdapter, DBusAdapterTypeSeq
    from .method import MethodCls
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


class NoMethodsWarning(UserWarning):
    """Issued if no methods are selected for a Mode; e.g. when user tries to
    activate a Mode using empty list as the methods. This is a subclass of
    `UserWarning <https://docs.python.org/3/library/exceptions.html#UserWarning>`_."""


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


class ContextAlreadyEnteredError(RuntimeError):
    """Raised if the context of a :class:`Mode` is already entered. This is a
    subclass of `RuntimeError <https://docs.python.org/3/library/exceptions.html#RuntimeError>`_.
    """


class Mode:
    """Mode instances are the most important objects, and they provide the main
    API of wakepy for the user. Typically, :class:`Mode` instances are created
    with the factory functions like :func:`keep.presenting \\
    <wakepy.keep.presenting>` and :func:`keep.running <wakepy.keep.running>`

    The Mode instances are `context managers \\
    <https://peps.python.org/pep-0343/>`_, which means that they can be used
    with the `with` statement, like this::

        with keep.running() as m:
            type(m) # <class 'wakepy.Mode'>

    For more information about how to use the Mode instances, see the
    :ref:`user-guide-page`.
    """

    name: str | None
    """The name of the mode. Examples: "keep.running" for the
    :func:`keep.presenting <wakepy.keep.presenting>` mode and "keep.presenting"
    for the :func:`keep.running <wakepy.keep.running>` mode.
    """

    active: bool
    """``True`` if the mode is active. Otherwise, ``False``. See also:
    :attr:`active_method`."""

    result: ActivationResult
    """The activation result which tells more about the activation process
    outcome. See :class:`ActivationResult`.

    .. versionchanged:: 1.0.0
        Renamed from ``activation_result`` to ``result``.
    """

    method: MethodInfo | None
    """The :class:`MethodInfo` representing the currenly used (active) or
    previously used (already deactivated) Method. ``None`` if the Mode has not
    ever been succesfully activated. See also :attr:`active_method`.

    .. versionadded:: 1.0.0

        The ``method`` attribute was added in wakepy 1.0.0 to replace the
        deprecated :attr:`used_method` attribute. """

    active_method: MethodInfo | None
    """The :class:`MethodInfo` representing the currenly used (active) Method.
    ``None`` if the Mode is not active. See also :attr:`used_method`.

    .. versionchanged:: 1.0.0

        The ``active_method`` is now a ``MethodInfo`` instance instead of
        a ``str`` representing the method name. """

    on_fail: OnFail
    """Tells what the mode does in case the activation fails. This can be
    "error", "warn", "pass" or a callable. If "error", raises
    :class:`ActivationError`. If "warn", issues a :class:`ActivationWarning`.
    If "pass", does nothing. If ``on_fail`` is a callable, it is called with
    an instance of :class:`ActivationResult`. For mode information, refer to
    the :ref:`on-fail-actions-section` in the user guide."""

    methods_priority: Optional[MethodsPriorityOrder]
    """The priority order for the methods to be used when entering the Mode.
    For more detailed explanation, see the ``methods_priority`` argument of the
    :func:`keep.presenting <wakepy.keep.presenting>` or :func:`keep.running \\
    <wakepy.keep.running>` factory functions.
    """

    _method_classes: list[Type[Method]]
    """The list of methods associated for this mode as given when creating the
    ``Mode``. For details, see the documentation of  ``methods`` in the
    ``Mode.__init__()`` method.
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
            "error", raises :class:`~wakepy.ActivationError`. Is selected
            "warn", issues a warning. If "pass", does nothing. If ``on_fail``
            is a callable, it must take one positional argument: result, which
            is an instance of :class:`ActivationResult`. The ActivationResult
            contains more detailed information about the activation process.
        dbus_adapter:
            For using a custom dbus-adapter. Optional. If not given, the
            default dbus adapter is used, which is
            :class:`~wakepy.dbus_adapters.jeepney.JeepneyDBusAdapter`
        """
        self.active: bool = False
        self.result = ActivationResult([])
        self.name = name
        self._method_classes = method_classes

        self._method: Method | None = None
        """This holds the used method instance. The used method instance will
        not be set to None when deactivating."""
        self.method: MethodInfo | None = None

        self._active_method: Method | None = None
        """This holds the active method instance"""
        self.active_method: MethodInfo | None = None

        self.heartbeat: Heartbeat | None = None

        self._dbus_adapter_cls = dbus_adapter
        # Retrieved and updated using the _dbus_adapter property
        self._dbus_adapter_instance: DBusAdapter | None = None
        self._dbus_adapter_created: bool = False

        self.on_fail = on_fail
        self.methods_priority = methods_priority

        self._has_entered_context: bool = False
        """This is used to track if the mode has been entered already. Set to
        True when activated, and to False when deactivated. A bit different
        from `active`, because you might be entered into a mode which fails,
        so `active` can be False even if this is True. """

    @classmethod
    def _from_name(
        cls,
        mode_name: ModeName | str,
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
        mode_name: str | ModeName
            The name of the mode to create. Must be an existing, registered
            Mode name, which means that there must be at least one subclass of
            :class:`~wakepy.core.method.Method` which has the
            :attr:`~wakepy.Method.mode_name` class attribute set to
            `mode_name`. Examples: "keep.running", "keep.presenting".
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

        logger.debug(
            'Creating wakepy mode "%s" with methods=%s, omit=%s, methods_priority=%s, on_fail=%s, dbus_adapter=%s',  # noqa E501
            mode_name,
            methods,
            omit,
            methods_priority,
            on_fail,
            dbus_adapter,
        )
        methods_for_mode = get_methods_for_mode(mode_name)

        try:
            selected_methods = select_methods(
                methods_for_mode, use_only=methods, omit=omit
            )
        except UnrecognizedMethodNames as e:
            err_msg = (
                f'The following Methods are not part of the "{str(mode_name)}" Mode: '
                f"{e.missing_method_names}. Please check that the Methods are correctly"
                f' spelled and that the Methods are part of the "{str(mode_name)}" '
                "Mode. You may refer to full Methods listing at https://wakepy.readthedocs.io/stable/methods-reference.html."
            )
            raise UnrecognizedMethodNames(
                err_msg,
                missing_method_names=e.missing_method_names,
            ) from e

        logger.debug(
            'Found %d method(s) for mode "%s": %s',
            len(methods_for_mode),
            mode_name,
            methods_for_mode,
        )
        selected_methods = select_methods(methods_for_mode, use_only=methods, omit=omit)

        logger.debug(
            'Selected %d method(s) for mode "%s": %s',
            len(selected_methods),
            mode_name,
            selected_methods,
        )
        if methods_for_mode and (not selected_methods):
            warn_text = (
                f'No methods selected for mode "{mode_name}"! This will lead to automatic failure of mode activation. '  # noqa E501
                f"To suppress this warning, select at least one of the available methods, which are: {methods_for_mode}"  # noqa E501
            )
            warnings.warn(warn_text, NoMethodsWarning, stacklevel=3)

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
        if self.active:
            logger.info(
                'Activated wakepy mode "%s" with method: %s',
                self.name,
                self.active_method,
            )
        else:
            logger.info(
                self.result.get_failure_text(newlines=False),
            )
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
        if self._has_entered_context:
            raise ContextAlreadyEnteredError(
                "A Mode can only be activated once! If "
                "you need to activate two Modes, you need to use two separate Mode "
                "instances."
            )

        method_classes = add_fake_success_if_required(
            self._method_classes, os.environ.get(WAKEPY_FAKE_SUCCESS)
        )
        method_classes_ordered = order_methods_by_priority(
            method_classes, self.methods_priority
        )

        logger.info(
            'Activating wakepy mode "%s". Will try the following methods in this order: %s',  # noqa E501
            self.name,
            [m.name for m in method_classes_ordered],
        )
        methodresults, self._active_method, self.heartbeat = (
            self._activate_one_of_methods(
                method_classes=method_classes_ordered,
                dbus_adapter=self._dbus_adapter,
            )
        )
        self.active_method = (
            MethodInfo._from_method(self._active_method)
            if self._active_method
            else None
        )

        self.result = ActivationResult(methodresults, mode_name=self.name)
        self.active = self.result.success
        self._method = self._active_method
        self.method = self.active_method

        if not self.active:
            handle_activation_fail(self.on_fail, self.result)

        self._has_entered_context = True
        return self.result

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
            active_method = methodcls(**method_kwargs)
            methodresult, heartbeat = activate_method(active_method)
            methodresults.append(methodresult)
            if methodresult.success:
                break
        else:
            # Tried activate with all methods, but none of them succeed
            active_method, heartbeat = None, None

        # Add unused methods to the results
        for methodcls in method_classes:
            unused_method = methodcls(**method_kwargs)
            method_info = MethodInfo._from_method(unused_method)
            methodresults.append(
                MethodActivationResult(method=method_info, success=None)
            )

        return methodresults, active_method, heartbeat

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
        self.active_method = None
        self.heartbeat = None
        self.active = False
        self._has_entered_context = False
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
    def activation_result(self) -> ActivationResult:  # pragma: no cover
        """
        .. deprecated:: 1.0.0
            Use :attr:`result` instead. This property will be removed in a
            future version of wakepy."""
        warnings.warn(
            "'Mode.activation_result' is deprecated in wakepy 1.0.0 and will be "
            "removed in a future version. Use 'Mode.result', instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.result

    @property
    def used_method(self) -> str | None:  # pragma: no cover
        """
        .. deprecated:: 1.0.0
            Use :attr:`method` instead. This property will be removed in a
            future version of wakepy."""
        warnings.warn(
            "'Mode.used_method' is deprecated in wakepy 1.0.0 and will be "
            "removed in a future version. Use 'Mode.method', instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.method.name if self.method else None


class UnrecognizedMethodNames(ValueError):
    """Raised if a method name is not recognized. This can happen if the
    method name is not part of the Methods used for a Mode. Typically this
    is caused by a typo, or mixing methods of different Modes (e.g.
    keep.presenting and keep.running).
    """

    def __init__(self, message: str, missing_method_names: StrCollection) -> None:
        """Initialize the UnrecognizedMethodName exception with a message."""
        super().__init__(message)
        self.message = message
        self.missing_method_names = missing_method_names


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
            raise UnrecognizedMethodNames(
                f"Methods {missing} in `use_only` are not part of `methods`!",
                missing_method_names=missing,
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
        warnings.warn(result.get_failure_text(), ActivationWarning, stacklevel=4)
        return
    elif on_fail == "error":
        raise ActivationError(result.get_failure_text())
    elif not callable(on_fail):
        raise ValueError(
            'on_fail must be one of "error", "warn", pass" or a callable which takes '
            "single positional argument (ActivationResult)"
        )
    on_fail(result)
