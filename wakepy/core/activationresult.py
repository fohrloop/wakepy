from __future__ import annotations

import os
import typing
from dataclasses import dataclass
from functools import wraps

from .constant import StringConstant
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


@dataclass(frozen=True)
class PlatformSupportStageInfo:
    failed: Tuple[Method, ...]
    passed: Tuple[Method, ...]


@dataclass(frozen=True)
class RequirementsStageInfo:
    failed: Tuple[Method, ...]
    passed: Tuple[Method, ...]
    unknown: Tuple[Method, ...]
    failure_reasons: Tuple[str, ...]

    def __post_init__(self):
        if not len(self.failure_reasons) == len(self.failed):
            raise ValueError(
                "The length of failure_reasons must equal to the length of failed Methods."
            )


@dataclass(frozen=True)
class BeforeActivateStageInfo:
    # This is another view to same data as available already from
    # PlatformSupportStageInfo and RequirementsStageInfo
    unsuitable: Tuple[Method, ...]
    unsuitability_reasons: Tuple[str, ...]
    potentially_suitable: Tuple[Method, ...]


@dataclass(frozen=True)
class ActivateStageInfo:
    passed: Tuple[Method, ...]
    failed: Tuple[Method, ...]
    failure_exceptions: Tuple[Exception, ...]
    unused: Tuple[Method, ...]

    def __post_init__(self):
        if not len(self.failure_exceptions) == len(self.failed):
            raise ValueError(
                "The length of failure_exceptions must equal to the length of failed Methods."
            )


@dataclass(frozen=True)
class ActivationStagesInfo:
    platform_support: PlatformSupportStageInfo
    requirements: RequirementsStageInfo
    _before_activate: BeforeActivateStageInfo
    activate: ActivateStageInfo


class StageName(StringConstant):
    ALL_METHODS = "1-get-all-methods"
    PLATFORM_SUPPORT = "2-check-platform-support"
    REQUIREMENTS = "3-check-requirements"
    ACTIVATION = "4-try-activation"


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

    # The minimum and maximum waiting times for waiting data from Queue
    # (seconds). These are used to calculate the timeout, if timeout is not
    # provided

    _default_timeout_minimum = 3
    _default_timeout_maximum = 8
    _default_time_per_method = 0.3  # 300ms

    def require_results(func):
        # TODO: add docs
        @wraps(func)
        def decorated_function(self, *args, **kwargs):
            if not self._results_set:
                self._get_and_set_mode_enter_results()
            return func(self, *args, **kwargs)

        return decorated_function

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

        self._queue_thread = queue_thread
        self._results_set = False
        self._timeout = (
            timeout
            if timeout is not None
            else self._get_default_timeout(len(candidate_methods))
        )

        self.stages: ActivationStagesInfo | None = None
        self.used_methods: Tuple[Method, ...] | None = None
        self.unused_methods: Tuple[Method, ...] | None = None
        self.failed_methods: Tuple[Method, ...] | None = None

        self.failure_reasons: Tuple[Tuple[StageName, str], ...] | None = None

        # Same methods as in used, unused and failed. In priority order.
        self.all_methods: Tuple[Method, ...] | None = None

    @property
    def real_success(self) -> bool:
        return len(self.success) > 0

    @property
    def success(self) -> bool:
        return self.real_success or should_fake_success()

    @property
    def failure(self) -> bool:
        return not self.success

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

    def _get_default_timeout(self, n_methods: int) -> float:
        """Calculates some sort of sane timeout for the blocking Queue.get
        calls. Depends on the number of candidate methods `n_methods`.
        """
        timeout_based_on_number_of_methods = n_methods * self._default_time_per_method
        return min(
            self._default_timeout_maximum,
            max(self._default_timeout_minimum, timeout_based_on_number_of_methods),
        )
