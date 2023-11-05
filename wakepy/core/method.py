from __future__ import annotations

import typing
import warnings
from abc import ABC, ABCMeta
from typing import Any

from wakepy.core import DbusMethodCall

from . import SystemName as SystemName
from .constant import StringConstant, auto

if typing.TYPE_CHECKING:
    from typing import Optional, Tuple

    from wakepy.core import Call
    from wakepy.io.dbus import DbusAdapter


class MethodError(Exception):
    """Occurred inside wakepy.core.method.Method"""


class EnterModeError(MethodError):
    """Occurred during method.enter_mode()"""


class ExitModeError(MethodError):
    """Occurred during method.exit_mode()"""


class HeartbeatCallError(MethodError):
    """Occurred during method.heartbeat()"""


class MethodMeta(ABCMeta):
    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("has_enter", "has_exit", "has_heartbeat"):
            raise AttributeError(f'Cannot set read-only attribute "{name}"!')
        return super().__setattr__(name, value)


class MethodOutcome(StringConstant):
    NOT_IMPLEMENTED = auto()
    SUCCESS = auto()


class SuitabilityCheckResult(StringConstant):
    # Uused when it is known for sure that a method is not suitable
    UNSUITABLE = auto()
    # Used when it can't be proben that a method is not suitable, but still it
    # has not tested if the method is suitable or not. For example, if a
    # subclass of Method does not implement `test_suitability()`
    POTENTIALLY_SUITABLE = auto()
    # Used when it has been tested, with `test_suitability`, that a method
    # should be supported. For example, if a method needs executable called
    # `foo`, version >=4.12, and an executable called `foo` was found in PATH
    # and the version was 4.16. So, This is the best quess that the method
    # should be suitable for the use case.
    SUITABLE = auto()


class UnsuitabilityTag(StringConstant):
    """These are used to distiguish between different reasons for unsuitability

    SYSTEM: Used when system is not supported by the method.
    """

    SYSTEM = auto()
    OTHER = auto()


class Suitability(typing.NamedTuple):
    result: SuitabilityCheckResult
    tag: Optional[UnsuitabilityTag]
    extrainfo: Optional[str]


class Method(ABC, metaclass=MethodMeta):
    """Methods are objects that are used to switch modes. The phases for
    changing and being in a Mode is:

    1) enter into a mode by calling enter_mode()
    2) keep into a mode by calling heartbeat() periodically
    3) exit froma mode by calling exit_mode()

    Typically one would either implement:
     * enter_mode() and exit_mode()  or just
     * heartbeat(),

    but also the hybrid option is possible.
    """

    supported_systems: Tuple[SystemName] = tuple()
    """All the supported systems. If a system is not listed here, this method
    if not going to be used on the system (when used as part of a Mode)
    
    Modify this in the subclass"""

    description: Optional[str] = None
    """Human-readable description for the method. Markdown allowed. Used to
    create documentation.
    """

    def __init__(self, dbus_adapters: Optional[Tuple[DbusAdapter, ...]] = None):
        self._dbus_adapters = dbus_adapters
        self.mode_switch_exception: Exception | None = None
        """Holds the possible exception caused by trying to switch to a mode
        using this method.
        """

        self.switch_success: bool | None = None
        """Tells if the switch to a Mode using the Method was successful or
        not."""

    def __init_subclass__(cls, **kwargs) -> None:
        """These are automatically added. They tell if the `enter_mode`,
        `exit_mode` and `heartbeat` methods are implemented in the Method
        subclass. (should not to touch these manually)"""

        cls._has_enter = cls.enter_mode is not Method.enter_mode
        cls._has_exit = cls.exit_mode is not Method.exit_mode
        cls._has_heartbeat = cls.heartbeat is not Method.heartbeat
        return super().__init_subclass__(**kwargs)

    heartbeat_period: int | float = 55
    """This is the amount of time (in seconds) between two consecutive calls of
    `heartbeat()`.
    """

    @property
    def name(self) -> str:
        return self.__class__.__qualname__

    def caniuse(
        self,
    ) -> Optional[bool] | UnsuitabilityTag | Tuple[UnsuitabilityTag, str]:
        """Tells if the Method is suitable or unsuitable. Implement this is a
        subclass. This is optional, but highly recommended. With `caniuse()` it
        is possible to give more information about why some Method is not
        supported.

        NOTE: You do not have to test for (operating) system here as it is
        automatically tested if Method has `supported_systems` attribute set!

        Examples
        --------
        - Test that system is running KDE using DbusMethodCalls to some service
          that should be running on KDE. Could also test that the version of
          KDE is something that is needed.
        - If a Method depends on availability of certain software on PATH,
          could test that it exist on PATH. (and that the version is suitable)

        Returns
        ------
        (a) If the Method is suitable, and can be used, return True.
        (b) If the result is uncertain, return None.
        (c) If the Method is unsuitable, you may return False, UnsuitabilityTag
        or tuple of (UnsuitabilityTag, str). The latter two options are
        recommended, as they also explains *why* the Method is unsuitable.
        """

    def enter_mode(self):
        """Enter to a Mode using this Method. Pair with a `exit_mode`.

        The .enter_mode() should always leave anything in a clean in case of
        errors; When subclassing, make sure that in case of any exceptions,
        everything is cleaned (and .exit_mode() does not need to be called.)
        """

    def heartbeat(self):
        """Called periodically, every `heartbeat_period` seconds."""

    def exit_mode(self):
        """Exit from a Mode using this Method. Paired with `enter_mode`

        When subclassing, pay special attention to the fact that `enter_mode()`
        should never raise any exceptions, unless something really is broken.
        This is because if any exceptions are raised in `method.enter_mode()`
        or `method.heartbeat()`, that method will simply not be used. But, if
        exceptions are risen in `method.exit_mode()`, there is no way to
        "correct" the situation (cannot just disregard the method and say:
        "sorry, I'm not sure about this but you're possibly stuck in the mode
         until you reboot").
        """

    def process_call(self, call: Call):
        if call is None:
            return

        if isinstance(call, DbusMethodCall):
            for dbus_adapter in self._dbus_adapters:
                try:
                    return dbus_adapter.process(call)
                except MethodError:
                    continue

        else:
            raise NotImplementedError(f"Cannot process a call of type: {type(call)}")

    def __str__(self):
        return f"<wakepy Method: {self.__class__.__name__}>"

    def __repr__(self):
        return f"<wakepy Method: {self.__class__.__name__} at {hex(id(self))}>"

    @property
    def has_enter(self):
        return self._has_enter

    @property
    def has_exit(self):
        return self._has_exit

    @property
    def has_heartbeat(self):
        return self._has_heartbeat

    def try_enter_mode(self) -> MethodOutcome:
        if not self.has_enter:
            return MethodOutcome.NOT_IMPLEMENTED
        try:
            self.enter_mode()
        except Exception as exc:
            raise EnterModeError from exc
        return MethodOutcome.SUCCESS

    def try_heartbeat(self) -> MethodOutcome:
        if not self.has_heartbeat:
            return MethodOutcome.NOT_IMPLEMENTED
        try:
            self.heartbeat()
        except Exception as exc:
            raise HeartbeatCallError from exc
        return MethodOutcome.SUCCESS

    def try_exit_mode(self) -> MethodOutcome:
        if not self.has_exit:
            return MethodOutcome.NOT_IMPLEMENTED
        try:
            self.exit_mode()
        except Exception as exc:
            raise ExitModeError from exc
        return MethodOutcome.SUCCESS

    def switch_to_the_mode(self) -> bool:
        """Try to use the Method to switch to a mode. Calls `enter_mode()` and
        `heartbeat()` and at least one of them must be implemented in the used
        Method subclass.

        Returns
        -------
        success:
            True, if switching to the mode succeeds (using enter_mode,
            heartbeat, or both). False if switching fails, for example
            because some 3rd party sw required by the method is missing (which
            is typically more common that succeeding)

        Side-effects
        -------------
        This sets the self.mode_switch_exception to an Exception if the mode
        switch was unsuccessful and to None if it was successful.

        Raises
        ------
        ExitModeError in the rare case where (1) enter_mode() and heartbeat()
        and exit_more() are all implemented and (2) enter_mode() succeeds and
        (3) heartbeat raises exception and (4) exit_mode() raises exception.

        MethodError in the (erroreously implemented) case where (1)
        enter_mode() and heartbeat() are both not implemented, and no successful
        switch is possible.

        """
        try:
            enter_outcome = self.try_enter_mode()
        except EnterModeError as exc:
            # In case of Exception during the enter, we don't try to do
            # anything else with the method. Not even exit. The
            # method.enter_mode() should always leave anything in a clean state
            # (esp. if exceptions arise). That is because it is impossible to
            # know how to clean anything from outside of the code inside of
            # `enter_mode`.
            self.mode_switch_exception = exc
            self.switch_success = False
            return self.switch_success

        try:
            heartbeat_outcome = self.try_heartbeat()
        except HeartbeatCallError as exc:
            # In the rare case where `enter_mode()` succeeds, *and* there
            # is a `heartbeat()` implementation *which raises exception*,
            # we mark it as failure, but we have to try to cancel the
            # effect of `enter_mode()`.
            self.try_exit_mode()
            self.mode_switch_exception = exc
            self.switch_success = False
            return self.switch_success

        # Here, no exceptions raised by `enter_mode()` or `heartbeat()`
        # A final check: At least one success
        if MethodOutcome.SUCCESS not in (enter_outcome, heartbeat_outcome):
            self.mode_switch_exception = MethodError(
                f"There was no implementation for enter_mode() or heartbeat() in {self}."
            )
            self.switch_success = False
            return self.switch_success

        self.mode_switch_exception = None
        self.switch_success = True
        return self.switch_success

    def get_suitability(
        self,
        system: SystemName | str,
    ) -> Suitability:
        """This is a method used to check the suitability of a method when
        running on a specific system with a set of software installed on it
        (which wakepy does not know beforehand).

        This method is not meant to be overridden in a subclass; override the
        .caniuse(), instead.

        Parameters
        ---------
        system:
            The system for which to check suitability. Usually, should be the
            CURRENT_SYSTEM (if not testing). Can als be a lower-case string
            like "windows", "linux" or "darwin".
        """

        if hasattr(self, "supported_systems") and system not in self.supported_systems:
            return Suitability(
                SuitabilityCheckResult.UNSUITABLE,
                UnsuitabilityTag.SYSTEM,
                f"Supported systems are: {self.supported_systems}. (detected system: {system})",
            )

        canuse = self.caniuse()
        if canuse is True:
            return Suitability(SuitabilityCheckResult.SUITABLE, None, None)
        elif canuse is None:
            return Suitability(SuitabilityCheckResult.POTENTIALLY_SUITABLE, None, None)
        elif canuse is False:
            return Suitability(
                SuitabilityCheckResult.UNSUITABLE,
                UnsuitabilityTag.UNSPECIFIED,
                None,
            )
        elif isinstance(canuse, UnsuitabilityTag):
            return Suitability(SuitabilityCheckResult.UNSUITABLE, canuse, None)

        if (
            isinstance(canuse, tuple)
            and len(canuse) == 2
            and isinstance(canuse[0], (UnsuitabilityTag, str))
            and isinstance(canuse[1], str)
        ):
            return Suitability(SuitabilityCheckResult.UNSUITABLE, canuse[0], canuse[1])

        warnings.warn(
            (
                f"""The caniuse() of {self} return value had an unexpected"""
                """ format. Disregarding the output and trying the Method anyway."""
            )
        )
        return Suitability(SuitabilityCheckResult.POTENTIALLY_SUITABLE, None, None)
