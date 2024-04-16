"""This module defines the Mode class and functions which may be used in the
activation and deactivation of Modes (using Methods).

Most important functions
------------------------
activate_method(method:Method) -> MethodActivationResult
    Activate a mode using a single Method
get_prioritized_methods
    Prioritize of collection of Methods
"""

from __future__ import annotations

import datetime as dt
import typing
import warnings
from typing import List, Sequence, Set, Union

from .activationresult import ActivationResult, MethodActivationResult
from .constants import PlatformName, StageName
from .dbus import DBusAdapter, get_dbus_adapter
from .heartbeat import Heartbeat
from .method import Method, MethodError, MethodOutcome
from .platform import CURRENT_PLATFORM
from .registry import get_method, get_methods_for_mode

if typing.TYPE_CHECKING:
    from types import TracebackType
    from typing import Callable, List, Literal, Optional, Set, Tuple, Type, Union

    from .constants import Collection, ModeName, StrCollection
    from .dbus import DBusAdapter, DBusAdapterTypeSeq
    from .method import Method, MethodCls

    OnFail = Literal["error", "warn", "pass"] | Callable[[ActivationResult], None]

    MethodClsCollection = Collection[MethodCls]


"""The strings in MethodsPriorityOrder are names of wakepy.Methods or the
asterisk ('*')."""
MethodsPriorityOrder = Sequence[Union[str, Set[str]]]


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

    activation_result: ActivationResult
    """The activation result which tells more about the activation process
    outcome.
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
        self.activation_result = ActivationResult()
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

    @classmethod
    def from_name(
        cls,
        modename: ModeName,
        methods: Optional[StrCollection] = None,
        omit: Optional[StrCollection] = None,
        methods_priority: Optional[MethodsPriorityOrder] = None,
        on_fail: OnFail = "error",
        dbus_adapter: Type[DBusAdapter] | DBusAdapterTypeSeq | None = None,
    ) -> Mode:
        """
        Creates and returns a Mode based on a mode name.

        Parameters
        ----------
        modename:
            The name of the mode to create. Used for debugging, logging,
            warning and error messages. Could be basically any string.
        methods: list, tuple or set of str
            The names of Methods to select from the mode defined with
            `modename`; a "whitelist" filter. Means "use these and only these
            Methods". Any Methods in `methods` but not in the selected mode
            will raise a ValueError. Cannot be used same time with `omit`.
            Optional.
        omit: list, tuple or set of str or None
            The names of Methods to remove from the mode defined with
            `modename`; a "blacklist" filter. Any Method in `omit` but not in
            the selected mode will be silently ignored. Cannot be used same
            time with `methods`. Optional.
        on_fail: "error" | "warn" | "pass" | Callable
            Determines what to do in case mode activation fails. Valid options
            are: "error", "warn", "pass" and a callable. If the option is
            "error", raises wakepy.ActivationError. Is selected "warn", issues
            warning. If "pass", does nothing. If `on_fail` is a callable, it
            must take one positional argument: result, which is an instance of
            ActivationResult. The ActivationResult contains more detailed
            information about the activation process.
        methods_priority: list[str | set[str]]
            The priority order, which is a list of method names or asterisk
            ('*'). The asterisk means "all rest methods" and may occur only
            once in the priority order, and cannot be part of a set. All method
            names must be unique and must be part of the `methods`.
        dbus_adapter:
            For using a custom dbus-adapter. Optional. If not given, the
            default dbus adapter is used, which is :class:`~wakepy.\\
            dbus_adapters.jeepney.JeepneyDBusAdapter`

        Returns
        -------
        mode: Mode
            The context manager for the selected mode.

        """
        methods_for_mode = get_methods_for_mode(modename)
        selected_methods = select_methods(methods_for_mode, use_only=methods, omit=omit)
        return cls(
            name=modename,
            methods=selected_methods,
            methods_priority=methods_priority,
            on_fail=on_fail,
            dbus_adapter=dbus_adapter,
        )


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


def activate_mode(
    methods: list[Type[Method]],
    dbus_adapter: Optional[DBusAdapter] = None,
    methods_priority: Optional[MethodsPriorityOrder] = None,
    modename: Optional[str] = None,
) -> Tuple[ActivationResult, Optional[Method], Optional[Heartbeat]]:
    """Activates a mode defined by a collection of Methods. Only the first
    Method which succeeds activation will be used, in order from highest
    priority to lowest priority.

    The activation may be faked as to be successful by using the
    WAKEPY_FAKE_SUCCESS environment variable.

    Parameters
    ----------
    methods:
        The list of Methods to be used for activating this Mode.
    dbus_adapter:
        Can be used to define a custom DBus adapter for processing DBus calls
        in the .caniuse(), .enter_mode(), .heartbeat() and .exit_mode() of the
        Method. Optional.
    methods_priority: list[str | set[str]]
        The priority order, which is a list of method names or asterisk
        ('*'). The asterisk means "all rest methods" and may occur only
        once in the priority order, and cannot be part of a set. All method
        names must be unique and must be part of the `methods`.
    modename:
        Name of the Mode. Used for communication to user, logging and in
        error messages (can be "any string" which makes sense to you).
        Optional.
    """
    check_methods_priority(methods_priority, methods)

    if not methods:
        # Cannot activate anything as there are no methods.
        return ActivationResult(modename=modename), None, None

    prioritized_methods = get_prioritized_methods(methods, methods_priority)
    # The fake method is always checked first (WAKEPY_FAKE_SUCCESS)
    prioritized_methods.insert(0, get_method("WAKEPY_FAKE_SUCCESS"))

    results = []

    for methodcls in prioritized_methods:
        method = methodcls(dbus_adapter=dbus_adapter)
        methodresult, heartbeat = activate_method(method)
        results.append(methodresult)
        if methodresult.success:
            break
    else:
        # Tried activate with all methods, but none of them succeed
        return ActivationResult(results, modename=modename), None, None

    # Activation was succesful.
    return ActivationResult(results, modename=modename), method, heartbeat


def check_methods_priority(
    methods_priority: Optional[MethodsPriorityOrder], methods: List[MethodCls]
) -> None:
    """Checks against `methods` that the `methods_priority` is valid.

    Parameters
    ----------
    methods_priority: list[str | set[str]]
        The priority order, which is a list of where items are method names,
        sets of methods names or the asterisk ('*'). The asterisk means "all
        rest methods" and may occur only once in the priority order, and cannot
        be part of a set. All method names must be unique and must be part of
        the `methods`.
    methods: list[MethodCls]
        The methods which the `methods_priority` is validated against.

    Raises
    ------
    ValueError or TypeError if the `methods_priority` is not valid.
    """
    if methods_priority is None:
        return

    known_method_names = {m.name for m in methods}
    known_method_names.add("*")
    seen_method_names = set()

    for method_name, in_set in _iterate_methods_priority(methods_priority):
        if not isinstance(method_name, str):
            raise TypeError("methods_priority must be a list[str | set[str]]!")

        if in_set and method_name == "*":
            raise ValueError(
                "Asterisk (*) may not be a part of a set in methods_priority!"
            )
        if method_name not in known_method_names:
            raise ValueError(
                f'Method "{method_name}" in methods_priority not in selected methods!'
            )
        if method_name in seen_method_names:
            if method_name != "*":
                raise ValueError(
                    f'Duplicate method name "{method_name}" in methods_priority'
                )
            else:
                raise ValueError(
                    "The asterisk (*) can only occur once in methods_priority!"
                )
        seen_method_names.add(method_name)


def _iterate_methods_priority(
    methods_priority: Optional[MethodsPriorityOrder],
) -> typing.Iterator[Tuple[str, bool]]:
    """Provides an iterator over the items in methods_priority. The items in
    the iterator are (method_name, in_set) 2-tuples, where the method_name is
    the method name (str) and the in_set is a boolean which is True if the
    returned method_name is part of a set and False otherwise."""

    if not methods_priority:
        return

    for item in methods_priority:
        if isinstance(item, set):
            for method_name in item:
                yield method_name, True
        else:
            yield item, False


def get_prioritized_methods_groups(
    methods: List[MethodCls], methods_priority: Optional[MethodsPriorityOrder]
) -> List[Set[MethodCls]]:
    """Prioritizes Methods in `methods` based on priority order defined by
    `methods_priority`. This function does not validate the methods_priority in
    any way; use `check_methods_priority` for validation of needed.

    Parameters
    ----------
    methods: list[MethodCls]
        The source list of methods. These methods are returned as prioritized
        groups.
    methods_priority: list[str | set[str]]
        The names of the methods in `methods`. This specifies the priority
        order; the order of method classes in the returned list. An asterisk
        ('*') can be used to denote "all other methods".


    Returns
    -------
    method_groups: list[set[MethodCls]]
        The prioritized methods. Each set in the output represents a group of
        equal priority. All Methods from the input `methods` are always
        included in the output


    Example
    -------
    Say there are methods MethodA, MethodB, MethodC, MethodD, MethodE, MethodF
    with names "A", "B", "C", "D", "E", "F":

    >>> methods = [MethodA, MethodB, MethodC, MethodD, MethodE, MethodF]
    >>> get_prioritized_methods_groups(
            methods,
            methods_priority=["A", "F", "*"]
        )
    [
        {MethodA},
        {MethodF},
        {MethodB, MethodC, MethodD, MethodE},
    ]

    """

    # Make this a list of sets just to make things simpler
    methods_priority_sets: List[Set[str]] = [
        {item} if isinstance(item, str) else item for item in methods_priority or []
    ]

    method_dct = {m.name: m for m in methods}

    asterisk = {"*"}
    asterisk_index = None
    out: List[Set[MethodCls]] = []

    for item in methods_priority_sets:
        if item == asterisk:
            # Save the location where to add the rest of the methods ('*')
            asterisk_index = len(out)
        else:  # Item is a set but not `asterisk`
            out.append({method_dct[name] for name in item})

    out_flattened = {m for group in out for m in group}
    rest_of_the_methods = {m for m in methods if m not in out_flattened}

    if rest_of_the_methods:
        if asterisk_index is not None:
            out.insert(asterisk_index, rest_of_the_methods)
        else:
            out.append(rest_of_the_methods)

    return out


def sort_methods_by_priority(methods: Set[MethodCls]) -> List[MethodCls]:
    """Sorts Method classes by priority and returns a new sorted list with
    Methods with highest priority first.

    The logic is:
    (1) Any Methods supporting the CURRENT_PLATFORM are placed before any other
        Methods (the others are not expected to work at all)
    (2) Sort alphabetically by Method name, ignoring the case
    """
    return sorted(
        methods,
        key=lambda m: (
            # Prioritize methods supporting CURRENT_PLATFORM over any others
            0 if CURRENT_PLATFORM in m.supported_platforms else 1,
            m.name.lower() if m.name else "",
        ),
    )


def get_prioritized_methods(
    methods: List[MethodCls],
    methods_priority: Optional[MethodsPriorityOrder] = None,
) -> List[MethodCls]:
    """Take an unordered list of Methods and sort them by priority using the
    methods_priority and automatic ordering. The methods_priority is used to
    define groups of priority (sets of methods). The automatic ordering part is
    used to order the methods *within* each priority group. In particular, all
    methods supported by the current platform are placed first, and all
    supported methods are then ordered alphabetically (ignoring case).

    Parameters
    ----------
    methods:
        The list of Methods to sort.
    methods_priority:
        Optional priority order, which is a list of method names (strings) or
        sets of method names (sets of strings). An asterisk ('*') may be used
        for "all the rest methods". None is same as ['*'].

    Returns
    -------
    sorted_methods:
        The input `methods` sorted with priority, highest priority first.

    Example
    -------
    Assuming: Current platform is Linux.

    >>> methods = [LinuxA, LinuxB, LinuxC, MultiPlatformA, WindowsA]
    >>> get_prioritized_methods(
    >>>    methods,
    >>>    methods_priority=[{"WinA", "LinuxB"}, "*"],
    >>> )
    [LinuxB, WindowsA, LinuxA, LinuxC, MultiPlatformA]

    Explanation:

    WindowsA and LinuxB were given high priority, but since the current
    platform is Linux, LinuxB was prioritized to be before WindowsA.

    The asterisk ('*') is converted to a set of rest of the methods:
    {"LinuxA", "LinuxC", "MultiPlatformA"}, and those are then
    automatically ordered. As all of them support Linux, the result is
    just the methods sorted alphabetically. The asterisk in the end is
    optional; it is added to the end of `methods_priority` if missing.

    """
    unordered_groups: List[Set[MethodCls]] = get_prioritized_methods_groups(
        methods, methods_priority=methods_priority
    )

    ordered_groups: List[List[MethodCls]] = [
        sort_methods_by_priority(group) for group in unordered_groups
    ]

    return [method for group in ordered_groups for method in group]


def activate_method(method: Method) -> Tuple[MethodActivationResult, Heartbeat | None]:
    """Activates a mode defined by a single Method.

    Returns
    -------
    result:
        The result of the activation process.
    heartbeat:
        If the `method` has method.heartbeat() implemented, and activation
        succeeds, this is a Heartbeat object. Otherwise, this is None.
    """
    if method.is_unnamed():
        raise ValueError("Methods without a name may not be used to activate modes!")

    result = MethodActivationResult(success=False, method_name=method.name)

    if not get_platform_supported(method, platform=CURRENT_PLATFORM):
        result.failure_stage = StageName.PLATFORM_SUPPORT
        return result, None

    requirements_fail, err_message = caniuse_fails(method)
    if requirements_fail:
        result.failure_stage = StageName.REQUIREMENTS
        result.failure_reason = err_message
        return result, None

    success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)
    if not success:
        result.failure_stage = StageName.ACTIVATION
        result.failure_reason = err_message
        return result, None

    result.success = True

    if not heartbeat_call_time:
        # Success, using just enter_mode(); no heartbeat()
        return result, None

    heartbeat = Heartbeat(method, heartbeat_call_time)
    heartbeat.start()

    return result, heartbeat


def deactivate_method(method: Method, heartbeat: Optional[Heartbeat] = None) -> None:
    """Deactivates a mode defined by the `method`.

    Raises
    ------
    MethodError (RuntimeError), if the deactivation was not successful.
    """

    heartbeat_stopped = heartbeat.stop() if heartbeat is not None else True

    if has_exit(method):
        errortxt = (
            f"The exit_mode of '{method.__class__.__name__}' ({method.name}) was "
            "unsuccessful! This should never happen, and could mean that the "
            "implementation has a bug. Entering the mode has been successful, and "
            "since exiting was not, your system might still be in the mode defined "
            f"by the '{method.__class__.__name__}', or not.  Suggesting submitting "
            f"a bug report and rebooting for clearing the mode. "
        )
        try:
            # The Method.exit_mode() *should* always return None. However, it
            # is not possible to control user created Methods implementation,
            # so this is a safety net for users not having strict static type
            # checking.
            retval = method.exit_mode()  # type: ignore[func-returns-value]
            if retval is not None:
                raise ValueError("exit_mode returned a value other than None!")
        except Exception as e:
            raise MethodError(errortxt + "Original error: " + str(e))

    if heartbeat_stopped is not True:
        raise MethodError(
            f"The heartbeat of {method.__class__.__name__} ({method.name}) could not "
            "be stopped! Suggesting submitting a bug report and rebooting for "
            "clearing the mode. "
        )


def get_platform_supported(method: Method, platform: PlatformName) -> bool:
    """Checks if method is supported by the platform

    Parameters
    ----------
    method: Method
        The method which platform support to check.
    platform:
        The platform to check against.

    Returns
    -------
    is_supported: bool
        If True, the platform is supported. Otherwise, False.
    """
    return platform in method.supported_platforms


def caniuse_fails(method: Method) -> tuple[bool, str]:
    """Check if the requirements of a Method are met or not.

    Returns
    -------
    (fail, message): (bool, str)
        If Method.caniuse() return True or None, the requirements check does
        not fail. In this case, return(False, '')

        If Method.caniuse() return False, or a string, the requirements check
        fails, and this function returns (True, message), where message is
        either the string returned by .caniuse() or emptry string.
    """

    try:
        canuse = method.caniuse()
    except Exception as exc:
        return True, str(exc)

    fail = False if (canuse is True or canuse is None) else True
    message = "" if canuse in {True, False, None} else str(canuse)

    return fail, message


def try_enter_and_heartbeat(method: Method) -> Tuple[bool, str, Optional[dt.datetime]]:
    """Try to use a Method to to activate a mode. First, with
    method.enter_mode(), and then with the method.heartbeat()

    Returns
    -------
    success, err_message, heartbeat_call_time
        A three-tuple, where success is boolean and True if activating the mode
        with the method was successful, otherwise False. The err_message is a
        string which may be non-empty only when success is False. The
        heartbeat_call_time is the datetime (in UTC) just before calling the
        method.hearbeat().

    Raises
    ------
    RunTimeError: In the rare edge case where the `method` has both,
    enter_mode() and heartbeat() defined, and the enter_mode() succeeds but the
    heartbeat() fails, which causes exit_mode() to be called, and if this
    exit_mode() also fails (as this leaves system uncertain state). All other
    Exceptions are handled (returning success=False).

    Detailed explanation
    --------------------
    These are the three possible statuses from attempts to use either
    enter_mode() or heartbeat():

    M: Missing implementation
    F: Failed attempt
    S: Succesful attempt

    There are total of 7 different outcomes (3*3 possibilities, minus two from
    not checking heartbeat if enter_mode fails), marked as
    {enter_mode_outcome}{heartbeat_outcome}; MS means enter_mode() was missing
    implementation and using heartbeat() was successful.

    All the possible combinations which may occur are

    outcome    What to do
    -------    ---------------------------------------------------------
     1)  F*    Return Fail + enter_mode error message

     2)  MM    Raise Exception -- the Method is faulty.
     3)  MF    Return Fail + heartbeat error message
     4)  MS    Return Success + heartbeat time

     5)  SM    Return Success
     6)  SF    Return Fail + heartbeat error message + call exit_mode()
     7)  SS    Return Success + heartbeat time

    """
    enter_outcome, enter_errmessage = _try_enter_mode(method)

    if enter_outcome == MethodOutcome.FAILURE:  # 1) F*
        return False, enter_errmessage, None

    hb_outcome, hb_errmessage, hb_calltime = _try_heartbeat(method)

    method_name = f"Method {method.__class__.__name__} ({method.name})"
    if enter_outcome == MethodOutcome.NOT_IMPLEMENTED:
        if hb_outcome == MethodOutcome.NOT_IMPLEMENTED:
            errmsg = (
                f"{method_name} is not properly defined! Missing implementation for "
                "both, enter_mode() and heartbeat()!"
            )
            return False, errmsg, None  # 2) MM
        elif hb_outcome == MethodOutcome.FAILURE:
            return False, hb_errmessage, None  # 3) MF
        elif hb_outcome == MethodOutcome.SUCCESS:
            return True, "", hb_calltime  # 4) MS

    elif enter_outcome == MethodOutcome.SUCCESS:
        if hb_outcome == MethodOutcome.NOT_IMPLEMENTED:  # 5) SM
            return True, "", None
        elif hb_outcome == MethodOutcome.FAILURE:  # 6) SF
            _rollback_with_exit(method)
            return False, hb_errmessage, None
        elif hb_outcome == MethodOutcome.SUCCESS:  # 7) SS
            return True, "", hb_calltime

    raise RuntimeError(  # pragma: no cover
        "Should never end up here. Check the return values for the enter_mode() and "
        f"heartbeat() of the {method_name}"
    )


def _try_enter_mode(method: Method) -> Tuple[MethodOutcome, str]:
    """Calls the method.enter_mode(). This function catches any possible
    Exceptions during the call."""

    if not has_enter(method):
        return MethodOutcome.NOT_IMPLEMENTED, ""

    outcome, err_message = _try_method_call(method, "enter_mode")

    return outcome, err_message


def _try_heartbeat(method: Method) -> Tuple[MethodOutcome, str, Optional[dt.datetime]]:
    """Calls the method.heartbeat(). This function catches any possible
    Exceptions during the call.

    Returns
    -------
    heartbeat_call_time: dt.datetime
        The UTC time just before the method.heartbeat() was called.
    """
    if not has_heartbeat(method):
        return MethodOutcome.NOT_IMPLEMENTED, "", None

    heartbeat_call_time = dt.datetime.now(dt.timezone.utc)
    outcome, err_message = _try_method_call(method, "heartbeat")

    return outcome, err_message, heartbeat_call_time


def _try_method_call(method: Method, mthdname: str) -> Tuple[MethodOutcome, str]:
    try:
        method_to_call = getattr(method, mthdname)
        retval = method_to_call()
        if retval is not None:
            raise ValueError(
                f"The {mthdname} of {method.__class__.__name__} ({method.name}) "
                f"returned an unsupported value {retval}. The only accepted return "
                "value is None"
            )
        outcome = MethodOutcome.SUCCESS
        err_message = ""
    except Exception as exc:
        err_message = repr(exc)
        outcome = MethodOutcome.FAILURE
    return outcome, err_message


def _rollback_with_exit(method: Method) -> None:
    """Roll back entering a mode by exiting it.

    Raises
    ------
    RuntimeError, if exit_mode fails (returns something else than None)

    Notes
    -----
    This function has the side effect of executing the calls in the
    method.exit_mode.
    """
    if not has_exit(method):
        # Nothing to exit from.
        return

    try:
        # The Method.exit_mode() *should* always return None. However, it
        # is not possible to control user created Methods implementation,
        # so this is a safety net for users not having strict static type
        # checking.
        exit_outcome = method.exit_mode()  # type: ignore[func-returns-value]
        if exit_outcome is not None:
            raise ValueError("exit_method did not return None")
    except Exception as exc:
        raise RuntimeError(
            f"Entered {method.__class__.__name__} ({method.name}) but could not exit!"
            + f" Original error: {str(exc)}"
        ) from exc


def has_enter(method: Method) -> bool:
    return type(method).enter_mode is not Method.enter_mode


def has_exit(method: Method) -> bool:
    return type(method).exit_mode is not Method.exit_mode


def has_heartbeat(method: Method) -> bool:
    return type(method).heartbeat is not Method.heartbeat


def handle_activation_fail(on_fail: OnFail, result: ActivationResult) -> None:
    if on_fail == "pass":
        return
    elif on_fail == "warn":
        warnings.warn(result.get_error_text())
        return
    elif on_fail == "error":
        raise ActivationError(result.get_error_text())
    elif not callable(on_fail):
        raise ValueError(
            'on_fail must be one of "error", "warn", pass" or a callable which takes '
            "single positional argument (ActivationResult)"
        )
    on_fail(result)
