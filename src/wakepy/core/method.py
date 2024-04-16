"""This module defines the Method class which is meant to be subclassed.

Method
* A class which is intended to be subclassed
* The Methods are ways of entering wakepy Modes.
"""

from __future__ import annotations

import sys
import typing
from abc import ABC
from typing import Type, cast

from .registry import register_method
from .strenum import StrEnum, auto

if sys.version_info < (3, 8):  # pragma: no-cover-if-py-gte-38
    from typing_extensions import Literal
else:  # pragma: no-cover-if-py-lt-38
    from typing import Literal


if typing.TYPE_CHECKING:
    from typing import Any, Optional, Tuple

    from wakepy.core import DBusAdapter, DBusMethodCall

    from .constants import ModeName, PlatformName

MethodCls = Type["Method"]


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


class MethodOutcome(StrEnum):
    NOT_IMPLEMENTED = auto()
    SUCCESS = auto()
    FAILURE = auto()


MethodOutcomeValue = Literal["NOT_IMPLEMENTED", "SUCCESS", "FAILURE"]


unnamed = "__unnamed__"
"""Constant for defining unnamed Method(s)"""


class Method(ABC):
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
    """The mode for the method. Each Method subclass may be registered to a
    single mode."""

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

    # waits for https://github.com/fohrloop/wakepy/issues/256
    # method_kwargs: Dict[str, object]
    """The method arguments. This is created from two parts

    1) The common_method_kwargs (if any)
    2) The method_kwargs[Method.name] (if any)

    These two dictionaries are merged. If the method_kwargs[Method.name]
    has same keys as common_method_kwargs, the values in
    method_kwargs[Method.name] have higher precedence, and they override
    the ones in common_method_kwargs for that particular Method.
    """

    def __init__(self, **kwargs: object) -> None:
        # The dbus-adapter may be used to process dbus calls. This is relevant
        # only on methods using D-Bus.
        self.dbus_adapter = cast("DBusAdapter | None", kwargs.pop("dbus_adapter", None))

        # waits for https://github.com/fohrloop/wakepy/issues/256
        # self.method_kwargs = kwargs

    def __init_subclass__(cls, **kwargs: object) -> None:
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

    def enter_mode(self) -> None:
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

    def exit_mode(self) -> None:
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

    def heartbeat(self) -> None:
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
        if self.dbus_adapter is None:
            raise RuntimeError(
                f'{self.__class__.__name__ } cannot process dbus method call "{call}" '
                "as it does not have a DBusAdapter."
            )
        return self.dbus_adapter.process(call)

    def __str__(self) -> str:
        return f"<wakepy Method: {self.__class__.__name__}>"

    def __repr__(self) -> str:
        return f"<wakepy Method: {self.__class__.__name__} at {hex(id(self))}>"

    @classmethod
    def is_unnamed(cls) -> bool:
        """Tells if the Method has a name or not. See also docs for
        `Method.name`.

        Returns
        -------
        True if the method is without a name. Otherwise False.
        """
        return cls.name == unnamed
