"""This module defines functions which may be used in the activation and
deactivation of Modes (using Methods).

Most important functions
------------------------
activate_using(method:Method) -> MethodActivationResult
    Activate a mode using a single Method 
get_prioritized_methods
    Prioritize of collection of Methods

Most important classes
----------------------
ActivationResult
    This is something returned from mode activation task. Contains the summary
    of all used methods, and whether the activation was successful or not.
MethodActivationResult
    One level lower than ActivationResult. This is result from activation task
    using a single Method.
"""
from __future__ import annotations

import datetime as dt
import os
import typing
from dataclasses import dataclass
from typing import List, Set, Union

from .calls import CallProcessor
from .constants import PlatformName
from .method import MethodError, MethodOutcome
from .platform import CURRENT_PLATFORM
from .strenum import StrEnum, auto

if typing.TYPE_CHECKING:
    from typing import Optional, Sequence, Tuple, Type

    from .method import Method, MethodCls

MethodsPriorityOrder = List[Union[str, Set[str]]]


class UsageStatus(StrEnum):
    FAIL = auto()
    SUCCESS = auto()
    UNUSED = auto()


class StageName(StrEnum):
    # These are stages which occur in order for each of the methods
    # when using a Method for activation.

    NONE = auto()  # No stage at all.

    # The stages in the activation process in order
    PLATFORM_SUPPORT = auto()
    REQUIREMENTS = auto()
    ACTIVATION = auto()


class ActivationResult:
    """The result returned by activating a mode, i.e. the `x` in
    `with mode as x: ...`.

    The ActivationResult is responsible of keeping track on successful and
    failed methods and providing different views on the results of the
    activation process. All results are lazily loaded; if you access any of the
    ActivationResult attributes, you will have to wait until the results
    are ready.

    Attributes
    ----------
    success: bool
        Tells is entering into a mode was successful. Note that this may be
        faked with WAKEPY_FAKE_SUCCESS environment variable e.g. for testing
        purposes.
    real_success: bool
        Tells is entering into a mode was successful. This
        may not faked with WAKEPY_FAKE_SUCCESS environment variable.
    failure: bool
        Always opposite of `success`. Included for convenience.
    active_methods: list[str]
        List of the names of all the successful (active) methods.
    active_methods_string: str
        A single string containing the names of all the successful (active)
        methods.


    Methods
    -------
    get_details:
        Get details of the activation results. This is the higher-level
        interface. If you want more control, use .get_detailed_results().
    get_detailed_results:
        Lower-level interface for getting details of the activation results.
        If you want easier access, use .get_details().
    """

    def __init__(self, results: Optional[List[MethodActivationResult]] = None):
        """
        Parameters
        ---------
        results:
            The MethodActivationResults to be used to fill the ActivationResult

        """
        self._results: list[MethodActivationResult] = results or []

    @property
    def real_success(self) -> bool:
        """Tells is entering into a mode was successful. This
        may not faked with WAKEPY_FAKE_SUCCESS environment variable.
        """
        for res in self._results:
            if res.status == UsageStatus.SUCCESS:
                return True
        return False

    @property
    def success(self) -> bool:
        """Tells is entering into a mode was successful.

        Note that this may be faked with WAKEPY_FAKE_SUCCESS environment
        variable (for tests). See also: real_success.

        """
        return self.real_success or should_fake_success()

    @property
    def failure(self) -> bool:
        """Always opposite of `success`. Included for convenience."""
        return not self.success

    @property
    def active_methods(self) -> list[str]:
        """List of the names of all the successful (active) methods"""
        return [
            res.method_name
            for res in self._results
            if res.status == UsageStatus.SUCCESS
        ]

    @property
    def active_methods_string(self) -> str:
        """A single string containing the names of all the successful (active)
        methods. For example:

        if `active_methods` is ['fist-method', 'SecondMethod',
        'some.third.Method'], the `active_methods_string` will be:
        'fist-method, SecondMethod & some.third.Method'
        """
        active_methods = self.active_methods
        if len(active_methods) == 1:
            return active_methods[0]
        return ", ".join(active_methods[:-1]) + f" & {active_methods[-1]}"

    def get_details(
        self,
        ignore_platform_fails: bool = True,
        ignore_unused: bool = False,
    ) -> list[MethodActivationResult]:
        """Get details of the activation results. This is the higher-level
        interface. If you want more control, use .get_detailed_results().

        Parameters
        ----------
        ignore_platform_fails:
            If True, ignores plaform support check fail. This is the default as
            usually one is not interested in methods which are meant for other
            platforms. If False, includes also platform fails. Default: True.
        ignore_unused:
            If True, ignores all unused / remaining methods. Default: False.
        """

        statuses = [
            UsageStatus.FAIL,
            UsageStatus.SUCCESS,
        ]
        if not ignore_unused:
            statuses.append(UsageStatus.UNUSED)

        fail_stages = [
            StageName.REQUIREMENTS,
            StageName.ACTIVATION,
        ]
        if not ignore_platform_fails:
            fail_stages.insert(0, StageName.PLATFORM_SUPPORT)
        return self.get_detailed_results(statuses=statuses, fail_stages=fail_stages)

    def get_detailed_results(
        self,
        statuses: Sequence[UsageStatus] = (
            UsageStatus.FAIL,
            UsageStatus.SUCCESS,
            UsageStatus.UNUSED,
        ),
        fail_stages: Sequence[StageName] = (
            StageName.PLATFORM_SUPPORT,
            StageName.REQUIREMENTS,
            StageName.ACTIVATION,
        ),
    ) -> list[MethodActivationResult]:
        """Get details of the activation results. This is the lower-level
        interface. If you want easier access, use .get_details().

        Parameters
        ----------
        statuses:
            The method usage statuses to include in the output. The options
            are "FAIL", "SUCCESS" and "UNUSED".
        fail_stages:
            The fail stages to include in the output. The options are
            "PLATFORM_SUPPORT", "REQUIREMENTS" and "ACTIVATION".
        """
        out = []
        for res in self._results:
            if res.status not in statuses:
                continue
            if res.status == UsageStatus.FAIL and res.failure_stage not in fail_stages:
                continue
            out.append(res)

        return out


@dataclass
class MethodActivationResult:
    """This class is a result from using a single Method to activate a mode."""

    status: UsageStatus

    method_name: str

    # None if the method did not fail. Otherwise, the name of the stage where
    # the method failed.
    failure_stage: Optional[StageName] = None

    message: str = ""

    def __repr__(self):
        error_at = " @" + self.failure_stage if self.failure_stage else ""
        message_part = f', "{self.message}"' if self.status == UsageStatus.FAIL else ""
        return f"({self.status}{error_at}, {self.method_name}{message_part})"


class Heartbeat:
    # TODO: This is just temporary dummy implementation.
    def __init__(
        self, method: Method, heartbeat_call_time: Optional[dt.datetime] = None
    ):
        self.method = method
        self.prev_call = heartbeat_call_time

    def start(self):
        ...


def activate(
    methods: list[Type[Method]],
    methods_priority: Optional[MethodsPriorityOrder] = None,
    call_processor: CallProcessor | None = None,
) -> Tuple[ActivationResult, Method, Heartbeat]:
    """Activates a mode defined by a collection of Methods. Only the first
    Method which succeeds activation will be used, in order from highest
    priority to lowest priority.

    Parameters
    ----------
    methods:
        The list of Methods to be used for activating this Mode.
    methods_priority: list[str | set[str]]
        The priority order, which is a list of method names or asterisk
        ('*'). The asterisk means "all rest methods" and may occur only
        once in the priority order, and cannot be part of a set. All method
        names must be unique and must be part of the `methods`.
    call_processor:
        The call processor to use for processing Calls in the .caniuse(),
        .enter_mode(), .heartbeat() and .exit_mode() of the Method. Used for
        example for using a custom Dbus library adapter. Optional.
    """
    call_processor = call_processor or CallProcessor()
    prioritized_methods = get_prioritized_methods(methods, methods_priority)
    results = []

    for methodcls in prioritized_methods:
        method = methodcls(call_processor=call_processor)
        methodresult = activate_using(method)
        results.append(methodresult)
        if methodresult.status == UsageStatus.SUCCESS:
            break

    return ActivationResult(results)


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
    """Provides an iterator over the items in methods_priority. The items in the
    iterator are (method_name, in_set) 2-tuples, where the method_name is the
    method name (str) and the in_set is a boolean which is True if the returned
    method_name is part of a set and False otherwise."""

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
    >>> get_prioritized_methods_groups(methods, methods_priority=["A", "F", "*"])
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
        elif isinstance(item, set):
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
    methods_priority and automatic ordering. The methods_priority is used to define
    groups of priority (sets of methods). The automatic ordering part is used
    to order the methods *within* each priority group. In particular, all
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


def activate_using(method: Method) -> Tuple[MethodActivationResult, Heartbeat | None]:
    """Activates a mode defined by a Method.

    Returns
    -------
    result:
        The result of the activation process.
    heartbeat:
        If the `method` has method.heartbeat() implemented, and activation
        succeeds, this is a Heartbeat object. Otherwise, this is None.
    """
    if method.name is None:
        raise ValueError("Methods without a name may not be used to activate modes!")

    result = MethodActivationResult(status=UsageStatus.FAIL, method_name=method.name)

    if not get_platform_supported(method, platform=CURRENT_PLATFORM):
        result.failure_stage = StageName.PLATFORM_SUPPORT
        return result, None

    requirements_fail, err_message = caniuse_fails(method)
    if requirements_fail:
        result.failure_stage = StageName.REQUIREMENTS
        result.message = err_message
        return result, None

    success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)
    if not success:
        result.failure_stage = StageName.ACTIVATION
        result.message = err_message
        return result, None

    result.status = UsageStatus.SUCCESS

    if not heartbeat_call_time:
        # Success, using just enter_mode(); no heartbeat()
        return result, None

    heartbeat = Heartbeat(method, heartbeat_call_time)
    heartbeat.start()

    return result, heartbeat


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

    canuse = method.caniuse()

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
    RunTimeError  (a) if the `method` is missing both, enter_mode() and
    heartbeat() implementation (Invalid Method definition) (b) the rare edge
    case where the `method` has both, enter_mode() and heartbeat() defined, and
    the enter_mode() succeeds but the heartbeat() fails, which causes
    exit_mode() to be called, and if this exit_mode() also fails (as this
    leaves system uncertain state).


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
        if hb_outcome == MethodOutcome.NOT_IMPLEMENTED:  # 2) MM
            raise MethodError(
                f"{method_name} is not properly defined! Missing implementation for "
                "both, enter_mode() and heartbeat()!"
            )
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
    if not method.has_enter:
        return MethodOutcome.NOT_IMPLEMENTED, ""

    retval = method.enter_mode()
    if not isinstance(retval, (bool, str)):
        raise MethodError(
            f"The enter_mode of {method.__class__.__name__} ({method.name}) returned a"
            " value of unsupported type. The supported types are: bool, str."
            f" Returned value: {retval}"
        )
    outcome = MethodOutcome.SUCCESS if retval is True else MethodOutcome.FAILURE
    message = retval if isinstance(retval, str) else ""

    return outcome, message


def _try_heartbeat(method: Method) -> Tuple[MethodOutcome, str, Optional[dt.datetime]]:
    """Calls the method.heartbeat()

    Returns
    -------
    heartbeat_call_time: dt.datetime
        The UTC time just before the method.heartbeat() was called.
    """
    if not method.has_heartbeat:
        return MethodOutcome.NOT_IMPLEMENTED, "", None

    heartbeat_call_time = dt.datetime.now(dt.timezone.utc)
    retval = method.heartbeat()

    if not isinstance(retval, (bool, str)):
        raise MethodError(
            f"The heartbeat of {method.__class__.__name__} ({method.name}) returned a"
            " value of unsupported type. The supported types are: bool, str."
            f" Returned value: {retval}"
        )
    outcome = MethodOutcome.SUCCESS if retval is True else MethodOutcome.FAILURE
    message = retval if isinstance(retval, str) else ""

    return outcome, message, heartbeat_call_time


def _rollback_with_exit(method):
    """Roll back entering a mode by exiting it.

    Raises
    ------
    RuntimeError, if exit_mode fails (returns something else than True)

    Notes
    -----
    This function has the side effect of executing the calls in the
    method.exit_mode.
    """
    if not method.has_exit:
        # Nothing to exit from.
        return

    exit_outcome = method.exit_mode()
    if exit_outcome is not True:
        raise RuntimeError(
            f"Entered {method.__class__.__name__} ({method.name}) but could not exit!"
        )


def should_fake_success() -> bool:
    """Function which says if fake success should be enabled

    Fake success is controlled via WAKEPY_FAKE_SUCCESS environment variable.
    If that variable is set to a truthy value,fake success is activated.

    Falsy values: '0', 'no', 'false' (case ignored)
    Truthy values: everything else

    Motivation:
    -----------
    When running on CI system, wakepy might fail to acquire an inhibitor lock
    just because there is no Desktop Environment running. In these cases, it
    might be useful to just tell with an environment variable that wakepy
    should fake the successful inhibition anyway. Faking the success is done
    after every other method is tried (and failed).
    """
    if "WAKEPY_FAKE_SUCCESS" not in os.environ:
        return False

    val_from_env = os.environ["WAKEPY_FAKE_SUCCESS"].lower()
    if val_from_env in ("0", "no", "false"):
        return False
    return True
