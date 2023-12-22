from __future__ import annotations

import os
import typing
from dataclasses import dataclass
from functools import wraps

from .constants import WorkerThreadMsgType
from .strenum import StrEnum, auto

if typing.TYPE_CHECKING:
    from queue import Queue
    from typing import Any, List, Optional, Sequence, Tuple

    from .activationmanager import ModeActivationManager
    from .method import Method


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
