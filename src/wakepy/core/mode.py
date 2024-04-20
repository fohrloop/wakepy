"""This module defines the Mode class and functions which may be used in the
activation and deactivation of Modes (using Methods).

Most important functions
------------------------
activate_method(method:Method) -> MethodActivationResult
    Activate a mode using a single Method
order_methods_by_priority
    Prioritize of collection of Methods
"""

from __future__ import annotations

import logging
import typing
import warnings
from typing import List, Sequence, Set, Union

from wakepy.core.constants import WAKEPY_FAKE_SUCCESS

from .activationresult import ActivationResult
from .dbus import DBusAdapter, get_dbus_adapter
from .heartbeat import Heartbeat
from .method import Method, activate_method, deactivate_method
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
        self.method_classes = methods
        self.active: bool = False
        self.activation_result = ActivationResult()
        self.name = name
        self.methods_priority = methods_priority
        self.on_fail = on_fail
        self.active_method: Method | None = None
        self.heartbeat: Heartbeat | None = None

        self._dbus_adapter_cls = dbus_adapter
        self._dbus_adapter: DBusAdapter | None = None

        self._logger = logging.getLogger(__name__)

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
        modename: str
            The name of the mode to create. Must be an existing Mode name;
            something that has used as Method.name attribute in a
            :class:`~wakepy.core.method.Method` subclass. Examples:
            "keep.running", "keep.presenting".
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
        # return None as type-checkers will mark code after with block
        # unreachable

        return False

    def _activate(self) -> ActivationResult:
        """Activates the mode with one of the methods which belong to the mode.
        The methods are used with descending priority; highest priority first,
        and the priority is determined with the mode.methods_priority.
        """
        if not self._dbus_adapter:
            self._dbus_adapter = get_dbus_adapter(self._dbus_adapter_cls)

        self.activation_result, self.active_method, self.heartbeat = activate_mode(
            methods=self.method_classes,
            methods_priority=self.methods_priority,
            dbus_adapter=self._dbus_adapter,
            modename=self.name,
        )
        self.active = self.activation_result.success

        if not self.active:
            handle_activation_fail(self.on_fail, self.activation_result)

        return self.activation_result

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
        MethodError (RuntimeError) if there was active method but an error
        occurred when trying to deactivate it."""

        if self.active:
            if self.active_method is None:
                raise RuntimeError(
                    f"Cannot deactivate mode: {str(self.name)}. The active_method is None! This should never happen."  # noqa E501
                )
            deactivate_method(self.active_method, self.heartbeat)
            deactivated = True
        else:
            deactivated = False

        self.active_method = None
        self.heartbeat = None
        self.active = False

        return deactivated


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

    if not methods:
        # Cannot activate anything as there are no methods.
        return ActivationResult(modename=modename), None, None

    prioritized_methods = order_methods_by_priority(methods, methods_priority)
    # The fake method is always checked first (WAKEPY_FAKE_SUCCESS)
    prioritized_methods.insert(0, get_method(WAKEPY_FAKE_SUCCESS))

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


def sort_methods_to_priority_groups(
    methods: List[MethodCls], methods_priority: Optional[MethodsPriorityOrder]
) -> List[Set[MethodCls]]:
    """Sorts Methods in `methods` to groups based on priority order defined by
    the given `methods_priority`.

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
    >>> sort_methods_to_priority_groups(
            methods,
            methods_priority=["A", "F", "*"]
        )
    [
        {MethodA},
        {MethodF},
        {MethodB, MethodC, MethodD, MethodE},
    ]

    """
    check_methods_priority(methods_priority, methods)

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


def order_methods_by_priority(
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
    >>> order_methods_by_priority(
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
    unordered_priority_groups: List[Set[MethodCls]] = sort_methods_to_priority_groups(
        methods, methods_priority=methods_priority
    )

    ordered_groups: List[List[MethodCls]] = [
        _order_set_of_methods_by_priority(group) for group in unordered_priority_groups
    ]

    return [method for group in ordered_groups for method in group]


def _order_set_of_methods_by_priority(methods: Set[MethodCls]) -> List[MethodCls]:
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
