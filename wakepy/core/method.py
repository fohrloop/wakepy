from __future__ import annotations

import typing
import warnings
from abc import ABC, ABCMeta
from dataclasses import dataclass, field
from typing import Any, List, Optional, Set, Tuple, Type, TypeVar

from wakepy.core import DbusMethodCall

from .calls import DbusMethodCall
from .constants import ModeName, SystemName
from .strenum import StrEnum, auto

if typing.TYPE_CHECKING:
    from wakepy.core import Call
    from wakepy.core.dbus import DbusAdapter


# type annotation shorthands
MethodCls = Type["Method"]
T = TypeVar("T")
Collection = List[T] | Tuple[T, ...] | Set[T]
MethodClsCollection = Collection[MethodCls]
StrCollection = Collection[str]

METHOD_REGISTRY: dict[str, MethodCls] = dict()
"""A name -> Method class mapping. Updated automatically; when python loads
a module with a subclass of Method, the Method class is added to this registry.
"""


def get_method(method_name: str) -> MethodCls:
    """Get a Method class based on its name."""
    if method_name not in METHOD_REGISTRY:
        raise KeyError(
            f'No Method with name "{method_name}" found!'
            " Check that the name is correctly spelled and that the module containing"
            " the class is being imported."
        )
    return METHOD_REGISTRY[method_name]


def get_methods(
    names: Collection[str] | None = None,
) -> Collection[MethodCls] | None:
    """Convert a collection (list, tuple or set) of method names to a
    collection of method classes"""
    if names is None:
        return None

    if isinstance(names, list):
        return [get_method(name) for name in names]
    elif isinstance(names, tuple):
        return tuple(get_method(name) for name in names)
    elif isinstance(names, set):
        return set(get_method(name) for name in names)

    raise TypeError("`names` must be a list, tuple or set")


def _register_method(cls: Type[Method]):
    """Registers a subclass of Method to the method registry"""

    if cls.name is None:
        # Methods without a name will not be registered
        return

    if cls.name in METHOD_REGISTRY:
        raise MethodDefinitionError(
            f'Duplicate Method name "{cls.name}": {cls.__qualname__} '
            f"(already registered to {METHOD_REGISTRY[cls.name].__qualname__})"
        )

    METHOD_REGISTRY[cls.name] = cls


class MethodError(RuntimeError):
    """Occurred inside wakepy.core.method.Method"""


class EnterModeError(MethodError):
    """Occurred during method.enter_mode()"""


class ExitModeError(MethodError):
    """Occurred during method.exit_mode()"""


class HeartbeatCallError(MethodError):
    """Occurred during method.heartbeat()"""


class MethodDefinitionError(RuntimeError):
    """Any error which is part of the Method (subclass) definition."""


class MethodMeta(ABCMeta):
    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("has_enter", "has_exit", "has_heartbeat"):
            raise AttributeError(f'Cannot set read-only attribute "{name}"!')
        return super().__setattr__(name, value)


class MethodOutcome(StrEnum):
    NOT_IMPLEMENTED = auto()
    SUCCESS = auto()


class SuitabilityCheckResult(StrEnum):
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


class UnsuitabilityTag(StrEnum):
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

    mode: ModeName | None = None
    """The mode for the method. Each method may be connected to single mode.
    Use None for methods which do not implement any mode."""

    supported_systems: Tuple[SystemName, ...] = tuple()
    """All the supported systems. If a system is not listed here, this method
    if not going to be used on the system (when used as part of a Mode)
    
    Modify this in the subclass"""

    description: Optional[str] = None
    """Human-readable description for the method. Markdown allowed. Used to
    create documentation.
    """

    name: str | None = None
    """Human-readable name for the method. Used by end-users to define
    the Methods used for entering a Mode, for example. If not None, must be
    unique across all Methods available in the python process. Set to None if
    the Method should not be listed anywhere (e.g. when Method is meant to be
    subclassed)."""

    # Set automatically. See __init_subclass__ and the properties named
    # similarly but without underscores.
    _has_enter: bool
    _has_exit: bool
    _has_heartbeat: bool

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
        _register_method(cls)

        return super().__init_subclass__(**kwargs)

    heartbeat_period: int | float = 55
    """This is the amount of time (in seconds) between two consecutive calls of
    `heartbeat()`.
    """

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

    def process_call(self, call: Optional[Call]):
        if call is None:
            return

        if isinstance(call, DbusMethodCall) and self._dbus_adapters:
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

    def activate_the_mode(self) -> bool:
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
                "There was no implementation for enter_mode() or heartbeat() in"
                f" {self}."
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
                f"Supported systems are: {self.supported_systems}. "
                f"(detected system: {system})",
            )

        canuse = self.caniuse()
        if canuse is True:
            return Suitability(SuitabilityCheckResult.SUITABLE, None, None)
        elif canuse is None:
            return Suitability(SuitabilityCheckResult.POTENTIALLY_SUITABLE, None, None)
        elif canuse is False:
            return Suitability(
                SuitabilityCheckResult.UNSUITABLE,
                UnsuitabilityTag.OTHER,
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


@dataclass
class MethodCurationOpts:
    """A container for options for selecting and prioritizing Methods.

    Purpose
    -------
    * Act as a data storage to method selection and prioritization parameters.
    * Provide basic validation for those input parameters
    * Convert the input parameters from strings to Method classes (constructor
      MethodCurationOpts.from_names)

    Rules
    -----
    1) Only possible to define one: `skip` ("blacklist") or `use_only`
      ("whitelist"), not both!
    2) A method can only be in `lower_priority` OR `higher_priority`, not both.
    3) A method can not be simultaneously skipped and prioritized
    """

    skip: MethodClsCollection = field(default_factory=list)
    use_only: MethodClsCollection = field(default_factory=list)
    lower_priority: MethodClsCollection = field(default_factory=list)
    higher_priority: MethodClsCollection = field(default_factory=list)

    def __post_init__(self):
        if self.skip and self.use_only:
            raise ValueError(
                "Can only define skip (blacklist) or use_only (whitelist), not both!"
            )

        methods_in_both = set(self.lower_priority).intersection(
            set(self.higher_priority)
        )
        if methods_in_both:
            raise ValueError(
                f"Cannot have same methods in higher_priority and lower_priority!"
                f" (Methods: {{{','.join(m.name for m in methods_in_both)}}})"
            )

        methods_with_set_priority = set(self.lower_priority).union(
            set(self.higher_priority)
        )
        skipped_with_priority = set(self.skip).intersection(methods_with_set_priority)
        if skipped_with_priority:
            raise ValueError(
                f"Cannot have same methods in `skip` and `higher_priority` or `lower_priority`!"
                f" (See methods: {{{','.join(m.name for m in skipped_with_priority)}}})"
            )

    @classmethod
    def from_names(
        cls,
        skip: Optional[StrCollection] = None,
        use_only: Optional[StrCollection] = None,
        lower_priority: Optional[StrCollection] = None,
        higher_priority: Optional[StrCollection] = None,
    ):
        return cls(
            skip=get_methods(skip) or [],
            use_only=get_methods(use_only) or [],
            lower_priority=get_methods(lower_priority) or [],
            higher_priority=get_methods(higher_priority) or [],
        )
