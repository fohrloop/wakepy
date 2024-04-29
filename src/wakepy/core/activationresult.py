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

    from .constants import ModeName


@dataclass
class ActivationResult:
    """Responsible of keeping track on the possibly successful (max 1), failed
    and unused methods and providing different view on the results of the
    activation process. The ``ActivationResult`` instances are created in
    activation process of a ``Mode`` like :func:`keep.presenting` and
    :func:`keep.running`, and one would not typically initialize one manually.

    **If you want to**:

    - Check if the activation was successful: See :attr:`success`
    - Check the active method: See :attr:`active_method`
    - Get information about activation failure in text format: See
      :meth:`get_failure_text`
    - Know more about the Methods involved: See :meth:`list_methods` and
      :meth:`query`.

    Parameters
    ----------
    results:
        The MethodActivationResults to be used to fill the ActivationResult
    mode_name:
        Name of the Mode. Optional.

    """

    results: InitVar[Optional[List[MethodActivationResult]]] = None
    # These are the results for each of the used wakepy.Methods, in the
    # order the methods were tried (first = highest priority, last =
    # lowest priority)

    mode_name: Optional[str] = None
    """Name of the :class:`Mode`. If the associated ``Mode`` does not have a
    name, the ``mode_name`` will be ``None``."""

    active_method: str | None = field(init=False)
    """The name of the active (successful) :class:`Method`. If no methods are
    active, this is ``None``."""

    success: bool = field(init=False)
    """Tells is entering into a mode was successful. Note that this may be
    faked with :ref:`WAKEPY_FAKE_SUCCESS` environment variable e.g. for testing
    purposes.

    See Also
    --------
    real_success, failure, get_failure_text
    """

    real_success: bool = field(init=False)
    """Tells is entering into a mode was successful. This
    may not faked with the :ref:`WAKEPY_FAKE_SUCCESS` environment variable.
    See also: :attr:`success`.
    """

    failure: bool = field(init=False)
    """Always opposite of :attr:`success`. Included for convenience. See also:
    :meth:`get_failure_text`.
    """

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
        want more control, use :meth:`~ActivationResult.query`. The
        returned methods are in the order as given in when initializing
        ActivationResult. If you did not create the ActivationReult manually,
        the methods are in the priority order; the highest priority methods
        (those which are/were tried first) are listed first.

        Parameters
        ----------
        ignore_platform_fails: bool
            If True, ignores plaform support check fail. This is the default as
            usually one is not interested in methods which are meant for other
            platforms. If False, includes also platform fails. Default:
            ``True``.
        ignore_unused: bool
            If True, ignores all unused / remaining methods. Default:
            ``False``.

        See Also
        --------
        query
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
        want easier access, use :meth:`~ActivationResult.list_methods`. The
        methods are in the order as given in when initializing
        ActivationResult. If you did not create the ActivationResult manually,
        the methods are in the priority order; the highest priority methods
        (those which are/were tried first) are listed first.

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

        See Also
        --------
        list_methods, get_failure_text
        """
        out = []
        for res in self._method_results:
            if res.success not in success:
                continue
            elif res.success is False and res.failure_stage not in fail_stages:
                continue
            out.append(res)

        return out

    def get_failure_text(self) -> str:
        """Gets information about a failure as text. In case the mode
        activation was successful, returns an empty string.

        This is only intended for interactive use. Users should not rely
        on the exact text format returned by this function as it may change
        without a notice. For programmatic use cases, it is advisable to use
        :meth:`query`, instead.

        See Also
        --------
        list_methods, query
        """

        if self.success:
            return ""
        debug_info = str(self.query())
        mode_name = self.mode_name or "[unnamed mode]"

        return (
            f'Could not activate Mode "{mode_name}"!\n\nMethod usage results, in '
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
    """The name of the :class:`Method` this result is for."""

    mode_name: ModeName | str
    """The name of the mode of the :class:`Method` this result is for."""

    success: bool | None
    """Tells about the result of the activation:

    - ``True``: Using Method was successful
    - ``False``: Using Method failed
    - ``None``: Method is unused
    """

    failure_stage: Optional[StageName] = None
    """None if the method did not fail. Otherwise, the name of the stage where
    the method failed.
    """

    failure_reason: str = ""
    """Empty string if activating the Method did not fail. Otherwise, failure
    reason as string, if provided."""

    def __repr__(self) -> str:
        error_at = " @" + self.failure_stage if self.failure_stage else ""
        failure_reason = f', "{self.failure_reason}"' if self.success is False else ""
        success_str = (
            "SUCCESS" if self.success else "FAIL" if self.success is False else "UNUSED"
        )
        return f"({success_str}{error_at}, {self.method_name}{failure_reason})"
