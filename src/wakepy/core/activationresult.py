"""This module defines the activation result classes.


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

import typing
from dataclasses import InitVar, dataclass, field
from typing import List, Sequence

from .constants import WAKEPY_FAKE_SUCCESS, StageName, StageNameValue

if typing.TYPE_CHECKING:
    from typing import Optional


@dataclass
class ActivationResult:
    """The ActivationResult is responsible of keeping track on the possibly
    successful (max 1), failed and unused methods and providing different views
    on the results of the activation process.

    Parameters
    ---------
    results:
        The MethodActivationResults to be used to fill the ActivationResult
    modename:
        Name of the Mode. Optional.

    Attributes
    ----------
    modename: str | None
        The name of the Mode. If the Mode did not have a name, the modename
        is None.
    success: bool
        Tells is entering into a mode was successful. Note that this may be
        faked with WAKEPY_FAKE_SUCCESS environment variable e.g. for testing
        purposes.
    real_success: bool
        Tells is entering into a mode was successful. This
        may not faked with WAKEPY_FAKE_SUCCESS environment variable.
    failure: bool
        Always opposite of `success`. Included for convenience.
    active_method: str | None
        The name of the the active (successful) method, if any.

    Methods
    -------
    list_methods:
        Get a list of the methods present in the activation process, and their
        activation results. This is the higher-level interface. If you want
        more control, use .query().
    query:
        Lower level interface for getting the list of the methods present in
        the activation process, and their activation results. If you want
        easier access, use .list_methods().
    """

    results: InitVar[Optional[List[MethodActivationResult]]] = None
    # These are the results for each of the used wakepy.Methods, in the
    # order the methods were tried (first = highest priority, last =
    # lowest priority)

    modename: Optional[str] = None
    """Name of the mode, if any."""

    active_method: str | None = field(init=False)
    """The name of the active (successful) method. If no methods are active,
    this is None."""

    success: bool = field(init=False)
    """Tells is entering into a mode was successful.

    Note that this may be faked with WAKEPY_FAKE_SUCCESS environment
    variable (for tests). See also: real_success.
    """

    real_success: bool = field(init=False)
    """Tells is entering into a mode was successful. This
    may not faked with WAKEPY_FAKE_SUCCESS environment variable.
    """

    failure: bool = field(init=False)
    """Always opposite of `success`. Included for convenience."""

    _method_results: List[MethodActivationResult] = field(init=False)

    def __post_init__(
        self,
        results: Optional[List[MethodActivationResult]] = None,
    ) -> None:
        self._method_results = results or []
        self.success = self._get_success()
        self.failure = not self.success
        self.real_success = self._get_real_success()
        self.active_method = self._get_active_method()

    def list_methods(
        self,
        ignore_platform_fails: bool = True,
        ignore_unused: bool = False,
    ) -> list[MethodActivationResult]:
        """Get a list of the methods present in the activation process, and
        their activation results. This is the higher-level interface. If you
        want more control, use .query(). The returned methods are in the order
        as given in when initializing ActivationResult. If you did not create
        the ActivationReult manually, the methods are in the priority order;
        the highest priority methods (those which are/were tried first) are
        listed first.

        Parameters
        ----------
        ignore_platform_fails:
            If True, ignores plaform support check fail. This is the default as
            usually one is not interested in methods which are meant for other
            platforms. If False, includes also platform fails. Default: True.
        ignore_unused:
            If True, ignores all unused / remaining methods. Default: False.
        """

        success_values = (True, False) if ignore_unused else (True, False, None)

        fail_stages = [StageName.REQUIREMENTS, StageName.ACTIVATION]
        if not ignore_platform_fails:
            fail_stages.insert(0, StageName.PLATFORM_SUPPORT)

        return self.query(success=success_values, fail_stages=fail_stages)

    def query(
        self,
        success: Sequence[bool | None] = (True, False, None),
        fail_stages: Sequence[StageName | StageNameValue] = (
            StageName.PLATFORM_SUPPORT,
            StageName.REQUIREMENTS,
            StageName.ACTIVATION,
        ),
    ) -> list[MethodActivationResult]:
        """Get a list of the methods present in the activation process, and
        their activation results. This is the lower-level interface. If you
        want easier access, use .list_methods(). The methods are in the order
        as given in when initializing ActivationResult. If you did not create
        the ActivationReult manually, the methods are in the priority order;
        the highest priority methods (those which are/were tried first) are
        listed first.

        Parameters
        ----------
        success:
            Controls what methods to include in the output. Options are:
            True (success), False (failure) and None (method not used). If
            `success = (True, False)`, returns only methods which did succeed
            or failer (do not return unused methods).
        fail_stages:
            The fail stages to include in the output. The options are
            "PLATFORM_SUPPORT", "REQUIREMENTS" and "ACTIVATION".
        """
        out = []
        for res in self._method_results:
            if res.success not in success:
                continue
            elif res.success is False and res.failure_stage not in fail_stages:
                continue
            out.append(res)

        return out

    def get_error_text(self) -> str:
        """Gets information about a failure as text. In case the mode
        activation was successful, returns an empty string."""

        if self.success:
            return ""
        debug_info = str(self.query())
        modename = self.modename or "[unnamed mode]"

        return (
            f'Could not activate Mode "{modename}"!\n\nMethod usage results, in '
            f"order (highest priority first):\n{debug_info}"
        )

    def _get_success(self) -> bool:
        for res in self._method_results:
            if res.success:
                return True
        return False

    def _get_real_success(self) -> bool:

        for res in self._method_results:
            if res.success and res.method_name != WAKEPY_FAKE_SUCCESS:
                return True
        return False

    def _get_active_method(self) -> str | None:
        methods = [res.method_name for res in self._method_results if res.success]
        if not methods:
            return None
        elif len(methods) == 1:
            return methods[0]
        else:
            raise ValueError(
                "The ActivationResult cannot have more than one active methods! "
                f"Active methods: {methods}"
            )


@dataclass
class MethodActivationResult:
    """This class is a result from using a single Method to activate a mode."""

    method_name: str

    # True: Using Method was successful
    # False: Using Method failed
    # None: Method is unused
    success: bool | None

    # None if the method did not fail. Otherwise, the name of the stage where
    # the method failed.
    failure_stage: Optional[StageName] = None

    failure_reason: str = ""

    def __repr__(self) -> str:
        error_at = " @" + self.failure_stage if self.failure_stage else ""
        failure_reason = f', "{self.failure_reason}"' if self.success is False else ""
        success_str = (
            "SUCCESS" if self.success else "FAIL" if self.success is False else "UNUSED"
        )
        return f"({success_str}{error_at}, {self.method_name}{failure_reason})"
