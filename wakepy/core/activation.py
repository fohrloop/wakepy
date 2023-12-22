"""This module defines functions which may be used in the activation and
deactivation of Modes (using Methods).

Most important functions
------------------------
activate_using(method:Method) -> MethodUsageResult
    Activate a mode using a single Method 

Most important classes
----------------------
ActivationResult
    This is something returned from mode activation task. Contains the summary
    of all used methods, and whether the activation was successful or not.
MethodUsageResult
    One level lower than ActivationResult. This is result from activation task
    using a single Method.
"""
from __future__ import annotations

import datetime as dt
import os
import typing
from dataclasses import dataclass

from .constants import PlatformName
from .method import MethodError, MethodOutcome
from .strenum import StrEnum, auto

if typing.TYPE_CHECKING:
    from typing import Optional, Sequence, Tuple

    from .activationmanager import ModeActivationManager
    from .method import Method


class UsageStatus(StrEnum):
    FAIL = auto()
    SUCCESS = auto()
    UNUSED = auto()


class StageName(StrEnum):
    # These are stages which occur in order for each of the methods
    # until the mode has been succesfully activated with "max number" of
    # methods

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

    def __init__(self, manager: ModeActivationManager):
        """
        Parameters
        ---------
        manager:
            The mode activation manager, which has methods for controlling and
            getting information about the mode activation process.
        """
        self._manager = manager
        self._results: list[MethodUsageResult] = []

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
    ) -> list[MethodUsageResult]:
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
    ) -> list[MethodUsageResult]:
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
class MethodUsageResult:
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
    def __init__(
        self, method: Method, heartbeat_call_time: Optional[dt.datetime] = None
    ):
        self.method = method
        self.prev_call = heartbeat_call_time

    def start(self):
        ...


def activate_using(method: Method) -> MethodUsageResult:
    result = MethodUsageResult(status=UsageStatus.FAIL, method_name=method.name)

    if not get_platform_supported(method):
        result.failure_stage = StageName.PLATFORM_SUPPORT
        return result

    requirements_fail, err_message = caniuse_fails(method)
    if requirements_fail:
        result.failure_stage = StageName.REQUIREMENTS
        result.message = err_message
        return result

    success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)
    if not success:
        result.failure_stage = StageName.ACTIVATION
        result.message = err_message

    if heartbeat_call_time:
        heartbeat = Heartbeat(method, heartbeat_call_time)
        heartbeat.start()

    return result


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

    if enter_outcome == MethodOutcome.SUCCESS:
        if hb_outcome == MethodOutcome.NOT_IMPLEMENTED:  # 5) SM
            return True, "", None
        if hb_outcome == MethodOutcome.FAILURE:  # 6) SF
            _rollback_with_exit(method)
            return False, hb_errmessage, None
        elif hb_outcome == MethodOutcome.SUCCESS:  # 7) SS
            return True, "", hb_calltime

    raise RuntimeError(
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
