from __future__ import annotations

import os
import typing
from dataclasses import dataclass
from functools import wraps

from .constant import StringConstant, auto
from .definitions import WorkerThreadMsgType

if typing.TYPE_CHECKING:
    from queue import Queue
    from typing import Any, List, Optional, Sequence, Tuple

    from .method import Method
    from .activationmanager import ModeActivationManager


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


class UsageStatus(StringConstant):
    FAIL = auto()
    SUCCESS = auto()
    UNUSED = auto()


class StageName(StringConstant):
    # These are stages which occur in order for each of the methods
    # until the mode has been succesfully activated with "max number" of
    # methods

    NONE = auto()  # No stage at all.

    # The stages in the activation process in order
    PLATFORM_SUPPORT = auto()
    REQUIREMENTS = auto()
    ACTIVATION = auto()


@dataclass(frozen=True)
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


# TODO:_ Move functionality to ModeActivationManager?
class ModeSwitcher:
    # The minimum and maximum waiting times for waiting data from Queue
    # (seconds). These are used to calculate the timeout, if timeout is not
    # provided

    timeout_minimum = 3
    timeout_maximum = 8
    timeout_per_method = 0.3  # 300ms

    def __init__(
        self,
        candidate_methods: List[Method],
        queue_thread: Queue,
        timeout: Optional[float | int] = None,
    ):
        """
        Parameters
        ---------
        candidate_methods:
            The list of candidate methods to be used to activate a Mode.
            These should be in priority order.
        queue_thread:
            The queue which is used to read data send by a ModeWorkerThread
        timeout:
            Timeout used when communicating with the associated thread (for
            example, when getting data from queues). In seconds. If not given,
            a default timeout is calculated based on the number of given
            `candidate_method`s.
        """
        self._results_set = False
        self._queue_thread = queue_thread
        self.timeout = timeout
        self._all_methods: Tuple[Method, ...] = tuple(candidate_methods)

    def require_results(func):
        # TODO: add docs
        @wraps(func)
        def decorated_function(self, *args, **kwargs):
            if not self._results_set:
                self._get_and_set_mode_enter_results()
            return func(self, *args, **kwargs)

        return decorated_function

    def get_timeout(self) -> float | int:
        """Gets the timeout for the blocking Queue.get calls.

        Either returns the timeout given in init, or, if that is missing,
        calculates some sort of sane value for it using the number of
        candidate methods `self.timeout_per_method`, `self.timeout_minimum` and
        `self.timeout_maximum`.
        """
        if self.timeout is not None:
            return self.timeout

        timeout_based_on_number_of_methods = (
            len(self.all_methods) * self.timeout_per_method
        )
        return min(
            self.timeout_maximum,
            max(self.timeout_minimum, timeout_based_on_number_of_methods),
        )

    def _get_and_set_mode_enter_results(self):
        msg_type: WorkerThreadMsgType
        arg: Any

        msg_type, arg = self._queue_thread.get(timeout=self._timeout)
        if msg_type == WorkerThreadMsgType.EXCEPTION:
            exc: Exception = arg

            raise RuntimeError(
                "Error during activating a mode. See the traceback for details"
            ) from exc
        if msg_type != WorkerThreadMsgType.OK:
            # Should never happen
            raise RuntimeError(f"Thread sent unknown data: {msg_type}, {arg}")

        self._results_set = True

        if not len(self.failure_reasons) == len(self.failed_methods):
            raise ValueError(
                "The length of `failure_reasons` must equal to the length of"
                " `failed_methods`."
            )


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
