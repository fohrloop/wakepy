from __future__ import annotations

import os
import typing
from dataclasses import dataclass
from functools import wraps

from .constant import StringConstant, auto
from .definitions import WorkerThreadMsgType

if typing.TYPE_CHECKING:
    from typing import Any, List, Optional, Tuple

    from .method import Method
    from queue import Queue


def should_fake_success() -> bool:
    """Function which says if fake success should be enabled

    Fake success is controlled via WAKEPY_FAKE_SUCCESS environment variable.
    If that variable is set to non-empty value, fake success is activated.

    Motivation:
    -----------
    When running on CI system, wakepy might fail to acquire an inhibitor lock
    just because there is no Desktop Environment running. In these cases, it
    might be useful to just tell with an environment variable that wakepy
    should fake the successful inhibition anyway. Faking the success is done
    after every other method is tried (and failed).
    """
    return bool(os.environ.get("WAKEPY_FAKE_SUCCESS"))


class SuccessStatus(StringConstant):
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
    status: SuccessStatus
    # None if the method did not fail. Otherwise, the name of the stage where
    # the method failed.
    failure_stage: Optional[StageName] = None
    method_name: str
    message: str = ""


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
                "The length of `failure_reasons` must equal to the length of `failed_methods`."
            )


class ActivationResult:
    """The result returned by activating a mode, i.e. the `x` in
    `with mode as x: ...`.

    The ActivationResult is responsible of track of successful and failed
    methods and providing different views on the results of the activation
    process. All results are lazily loaded; if you access any of the
    ActivationResult attributes, you will have to wait until the results
    are ready.

    Attributes
    ----------
    TODO: update these

    success: bool
        Tells is entering into a mode was successful. Note that this
        may be faked with WAKEPY_FAKE_SUCCESS environment variable.
    real_success: bool
        Tells is entering into a mode was successful. This
        may not faked with WAKEPY_FAKE_SUCCESS environment variable.
    failure: bool
        Always opposite of `success`. Included for convenience.
    """

    def __init__(self, switcher: ModeSwitcher):
        """
        Parameters
        ---------
        switcher:
            The mode switcher.
        """
        self._switcher = switcher
        self._data: list[MethodUsageResult] = []

        self.active_methods: list[str] = []

    @property
    def real_success(self) -> bool:
        return isinstance(self.used_methods, tuple) and len(self.used_methods) > 0

    @property
    def success(self) -> bool:
        return self.real_success or should_fake_success()

    @property
    def failure(self) -> bool:
        return not self.success
