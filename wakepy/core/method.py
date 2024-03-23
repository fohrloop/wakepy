"""This module defines the Method class and few functions for working with
methods

Method
* A class which is intended to be subclassed
* The Methods are ways of entering wakepy Modes.

General functions
-----------------
select_methods
    Select Methods from a collection based on a white- or blacklist.

"""

from __future__ import annotations

import typing
from abc import ABC, ABCMeta
from typing import Any, List, Optional, Set, Tuple, Type, TypeVar, Union

from .constants import ModeName, PlatformName
from .registry import register_method
from .strenum import StrEnum, auto

if typing.TYPE_CHECKING:
    from wakepy.core import DBusAdapter, DBusMethodCall

MethodCls = Type["Method"]
T = TypeVar("T")
Collection = Union[List[T], Tuple[T, ...], Set[T]]
MethodClsCollection = Collection[MethodCls]
StrCollection = Collection[str]


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
    FAILURE = auto()


MethodOutcomeValue = typing.Literal["NOT_IMPLEMENTED", "SUCCESS", "FAILURE"]


unnamed = "__unnamed__"
"""Constant for defining unnamed Method(s)"""


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

    mode: ModeName | str

    """The mode for the method. Each method may be connected to single mode.
    Use None for methods which do not implement any mode."""

    supported_platforms: Tuple[PlatformName, ...] = tuple()
    """All the supported platforms. If a platform is not listed here, this
    method is not going to be used on the platform (when used as part of a
    Mode). Modify this in the subclass"""

    description: Optional[str] = None
    """Human-readable description for the method. Markdown allowed. Used to
    create documentation.
    """

    name: str = unnamed
    """Human-readable name for the method. Used by end-users to define
    the Methods used for entering a Mode, for example. If given, must be
    unique across all Methods available in the python process. Leave unset if
    the Method should not be listed anywhere (e.g. when Method is meant to be
    subclassed)."""

    # Set automatically. See __init_subclass__ and the properties named
    # similarly but without underscores.
    _has_enter: bool
    _has_exit: bool
    _has_heartbeat: bool

    def __init__(self, dbus_adapter: Optional[DBusAdapter] = None):
        # The dbus-adapter may be used to process dbus calls. This is relevant
        # only on methods using D-Bus.
        self._dbus_adapter = dbus_adapter

    def __init_subclass__(cls, **kwargs) -> None:
        """These are automatically added. They tell if the `enter_mode`,
        `exit_mode` and `heartbeat` methods are implemented in the Method
        subclass. (should not to touch these manually)"""

        cls._has_enter = cls.enter_mode is not Method.enter_mode
        cls._has_exit = cls.exit_mode is not Method.exit_mode
        cls._has_heartbeat = cls.heartbeat is not Method.heartbeat
        register_method(cls)

        return super().__init_subclass__(**kwargs)

    def caniuse(
        self,
    ) -> bool | None | str:
        """Tells if the Method is suitable or unsuitable.

        Returns
        ------
        (a) If the Method is suitable, and can be used, return True.
        (b) If the result is uncertain, return None.
        (c) If the Method is unsuitable, may return False or a string.
            Returning a string is recommended, as it  also explains *why* the
            Method is unsuitable. May also simply raise an Exception, in which
            case the Exception message is used as failure reason.
        """

        # Notes for subclassing
        # =====================
        # This is optional, but highly recommended. With `caniuse()` it
        # is possible to give more information about why some Method is not
        # supported.

        # NOTE: You do not have to test for the current platform here as it is
        # automatically tested if Method has `supported_platforms` attribute
        # set!

        # Examples
        # --------
        # - Test that system is running KDE using DBusMethodCalls to some
        #   service that should be running on KDE. Could also test that the
        #   version of KDE is something that is needed.
        # - If a Method depends on availability of certain software on PATH,
        #   could test that it exist on PATH. (and that the version is
        #   suitable)

    def enter_mode(self):
        """Enter to a Mode using this Method. Pair with a `exit_mode`.

        Returns
        -------
        If entering the mode was successful, returns None. Otherwise, raises
        an Exception.

        Raises
        -------
        Could raise an Exception of any type.
        """

        # Notes for subclassing
        # =====================
        # The only acceptable return value from this method is None. Any other
        # return value is considered as an error.
        #
        # Errors
        # -------
        # If the mode enter was not succesful, raise an Exception of any type.
        # This is catched by the mode activation process and handled.
        #
        # Note: The .enter_mode() should always leave anything in a clean in
        # case of errors; When subclassing, make sure that in case of any
        # exceptions, everything is cleaned; everything should be left in
        # a state which does not require .exit_mode() to be called.
        #
        return

    def exit_mode(self):
        """Exit from a Mode using this Method. Paired with `enter_mode`

        Returns
        -------
        If exiting the mode was successful, or if there was no need to exit
        from the mode, returns None. Otherwise, raises an Exception.
        """

        # Notes for subclassing
        # =====================
        # The only acceptable return value from this method is None. Any other
        # return value is considered as an error.
        #
        # Pay special attention to the fact that `exit_mode()`
        # should never raise any exceptions, unless something really is broken.
        # This is because if any exceptions are raised in `method.enter_mode()`
        # or `method.heartbeat()`, that method will simply not be used. But, if
        # exceptions are risen in `method.exit_mode()`, there is no way to
        # "correct" the situation (cannot just disregard the method and say:
        # "sorry, I'm not sure about this but you're possibly stuck in the mode
        #  until you reboot").

        return

    heartbeat_period: int | float = 55
    """This is the amount of time (in seconds) between two consecutive calls of
    `heartbeat()`.
    """

    def heartbeat(self):
        """Called periodically, every `heartbeat_period` seconds.

        Returns
        -------
        If calling the heartbeat was successful, returns None. Otherwise,
        raises an Exception.
        """
        return

    def process_dbus_call(self, call: DBusMethodCall) -> Any:
        # Notes for subclassing
        # =====================
        # This method is always available for all subclasses of Method. This
        # can be used to get to call dbus methods and get return values. The
        # Method subclass does not have to get the _dbus_adapter from anywhere
        # as it is available automatically (if there is one). Any Exceptions
        # raised by this method does not need to be handled in the Method
        # subclass, either. Typically one would *not* override this method.
        if self._dbus_adapter is None:
            raise RuntimeError(
                f'{self.__class__.__name__ } cannot process dbus method call "{call}" '
                "as it does not have a DBusAdapter."
            )
        return self._dbus_adapter.process(call)

    @property
    def has_enter(self) -> bool:
        return self._has_enter

    @property
    def has_exit(self) -> bool:
        return self._has_exit

    @property
    def has_heartbeat(self) -> bool:
        return self._has_heartbeat

    def __str__(self):
        return f"<wakepy Method: {self.__class__.__name__}>"

    def __repr__(self):
        return f"<wakepy Method: {self.__class__.__name__} at {hex(id(self))}>"

    @classmethod
    def _is_unnamed(cls):
        return cls.name == unnamed


def select_methods(
    methods: MethodClsCollection,
    omit: Optional[StrCollection] = None,
    use_only: Optional[StrCollection] = None,
) -> List[MethodCls]:
    """Selects Methods from from `methods` using a blacklist (omit) or
    whitelist (use_only). If `omit` and `use_only` are both None, will return
    all the original methods.

    Parameters
    ----------
    methods: collection of Method classes
        The collection of methods from which to make the selection.
    omit: list, tuple or set of str or None
        The names of Methods to remove from the `methods`; a "blacklist"
        filter. Any Method in `omit` but not in `methods` will be silently
        ignored. Cannot be used same time with `use_only`. Optional.
    use_only: list, tuple or set of str
        The names of Methods to select from the `methods`; a "whitelist"
        filter. Means "use these and only these Methods". Any Methods in
        `use_only` but not in `methods` will raise a ValueErrosr. Cannot
        be used same time with `omit`. Optional.

    Returns
    -------
    methods: list[MethodCls]
        The selected method classes.

    Raises
    ------
    ValueError if the input arguments (omit or use_only) are invalid.
    """

    if omit and use_only:
        raise ValueError(
            "Can only define omit (blacklist) or use_only (whitelist), not both!"
        )
    elif omit is None and use_only is None:
        selected_methods = list(methods)
    elif omit is not None:
        selected_methods = [m for m in methods if m.name not in omit]
    elif use_only is not None:
        selected_methods = [m for m in methods if m.name in use_only]
        if not set(use_only).issubset(m.name for m in selected_methods):
            missing = sorted(set(use_only) - set(m.name for m in selected_methods))
            raise ValueError(
                f"Methods {missing} in `use_only` are not part of `methods`!"
            )
    else:  # pragma: no cover
        raise ValueError("Invalid `omit` and/or `use_only`!")
    return selected_methods
