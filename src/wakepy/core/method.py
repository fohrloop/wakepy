"""This module defines the Method class which is meant to be subclassed.

Method
* A class which is intended to be subclassed
* The Methods are ways of entering wakepy Modes.
"""

from __future__ import annotations

import datetime as dt
import sys
import typing
from abc import ABC
from typing import Type, cast

from .activationresult import MethodActivationResult
from .constants import PlatformName, StageName
from .heartbeat import Heartbeat
from .platform import CURRENT_PLATFORM
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

    1) enter into a mode by calling :meth:`enter_mode`
    2) keep into a mode by calling :meth:`heartbeat` periodically
    3) exit from a mode by calling :meth:`exit_mode`

    Typically one would either implement either :meth:`enter_mode` and
    :meth:`exit_mode`  or just :meth:`heartbeat`, but also the hybrid option
    is possible.
    """

    mode_name: ModeName | str
    """The name of the mode which the Method implements. Each Method subclass
    implements a single mode, but multiple Methods may implement the same mode.
    Setting ``Method.mode_name`` to `foo` on one or more ``Method`` subclasses
    defines the Mode `foo` (:class:`Mode` classes are themselves not defined or
    registered anywhere)"""

    supported_platforms: Tuple[PlatformName, ...] = (
        PlatformName.LINUX,
        PlatformName.WINDOWS,
        PlatformName.MACOS,
        PlatformName.OTHER,
    )
    """Lists the platforms the Method supports. If a platform is not listed in
    ``method.supported_platforms``, the ``method`` is not going to be used on
    the platform (when used as part of  a :class:`Mode`), and the Method
    activation result will show a fail in the "PLATFORM" stage.

    When subclassing, defining ``supported_platforms`` reduces some work
    required when writing the logic for :meth:`caniuse`.  Additionally, it aids
    in distinguishing the "PLATFORM" stage fail as a separate type of failure.

    Default: Support all platforms.
    """

    name: str = unnamed
    """Human-readable name for the method. Used to define the Methods used for
    entering a :class:`Mode`, for example. If given, must be unique across all
    Methods available in the python process for the :attr:`mode`. Left unset
    if the Method should not be listed anywhere (e.g. when Method is meant to
    be subclassed)."""

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
        -------
        result: bool | None | str
            ``True`` means suitable, ``None`` means uncertain, ``False`` means
            unsuitable and  a string means unsuitable and tells the reason for
            it.

        Raises
        ------
        Exception
            If the Method may not be used, may raise an Exception.
        """

        # Notes for subclassing
        # =====================
        # This is optional, but highly recommended. With `caniuse()` it
        # is possible to give more information about why some Method is not
        # supported.

        # Subclass return value
        # ---------------------
        # (a) If the Method is suitable, and can be used, return True.
        # (b) If the result is uncertain, return None.
        # (c) If the Method is unsuitable, may return False or a string.
        #     Returning a string is recommended, as it  also explains *why*
        #     the Method is unsuitable. May also simply raise an Exception, in
        #     which case the Exception message is used as failure reason.

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
        """Enter to a Mode using this Method. Pair with :meth:`exit_mode`.

        Returns
        -------
        None:
            If entering the mode was successful.

        Raises
        ------
        Exception
            If entering the mode was not succesful.
        """

        # Notes for subclassing
        # =====================
        # The only acceptable return value from this method is None. Any other
        # return value is considered as an error.
        #
        # Errors
        # -------
        # If the mode enter was not successful, raise an Exception of any type.
        # This is catched by the mode activation process and handled.
        #
        # Note: The .enter_mode() should always leave anything in a clean in
        # case of errors; When subclassing, make sure that in case of any
        # exceptions, everything is cleaned; everything should be left in
        # a state which does not require .exit_mode() to be called.
        #
        return

    def exit_mode(self) -> None:
        """Exit from a Mode using this Method. Paired with :meth:`enter_mode`.

        Returns
        -------
        None:
            If exiting the mode was successful, or if there was no need to exit
            from the mode.

        Raises
        ------
        Exception
            If exiting the mode was not succesful.
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
    :meth:`heartbeat`.
    """

    def heartbeat(self) -> None:
        """Called periodically, every :attr:`heartbeat_period` seconds.

        **NOTE** Heartbeat support is not yet implemented.

        Ticket: https://github.com/fohrloop/wakepy/issues/109

        Returns
        -------
        None:
            If calling the heartbeat was successful, returns None.

        Raises
        ------
        Exception
            If calling heartbeat was not successful.
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
        """Tells if the Method has a name or not. See also :attr:`name`.

        Returns
        -------
        result: bool
            ``True`` if the method is without a name. Otherwise ``False``.
        """
        return cls.name == unnamed


def activate_method(method: Method) -> Tuple[MethodActivationResult, Heartbeat | None]:
    """Activates a mode defined by a single Method.

    Returns
    -------
    result:
        The result of the activation process.
    heartbeat:
        If the `method` has method.heartbeat() implemented, and activation
        succeeds, this is a Heartbeat object. Otherwise, this is None.
    """
    if method.is_unnamed():
        raise ValueError("Methods without a name may not be used to activate modes!")

    result = MethodActivationResult(
        success=False, method_name=method.name, mode_name=method.mode_name
    )

    if not get_platform_supported(method, platform=CURRENT_PLATFORM):
        result.failure_stage = StageName.PLATFORM_SUPPORT
        return result, None

    requirements_fail, err_message = caniuse_fails(method)
    if requirements_fail:
        result.failure_stage = StageName.REQUIREMENTS
        result.failure_reason = err_message
        return result, None

    success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)
    if not success:
        result.failure_stage = StageName.ACTIVATION
        result.failure_reason = err_message
        return result, None

    result.success = True

    if not heartbeat_call_time:
        # Success, using just enter_mode(); no heartbeat()
        return result, None

    heartbeat = Heartbeat(method, heartbeat_call_time)
    heartbeat.start()

    return result, heartbeat


def deactivate_method(method: Method, heartbeat: Optional[Heartbeat] = None) -> None:
    """Deactivates a mode defined by method

    Raises
    ------
    RuntimeError, if the deactivation was not successful.
    """

    heartbeat_stopped = heartbeat.stop() if heartbeat is not None else True

    if has_exit(method):
        errortxt = (
            f"The exit_mode of '{method.__class__.__name__}' ({method.name}) was "
            "unsuccessful! This should never happen, and could mean that the "
            "implementation has a bug. Entering the mode has been successful, and "
            "since exiting was not, your system might still be in the mode defined "
            f"by the '{method.__class__.__name__}', or not.  Suggesting submitting "
            f"a bug report and rebooting for clearing the mode. "
        )
        try:
            # The Method.exit_mode() *should* always return None. However, it
            # is not possible to control user created Methods implementation,
            # so this is a safety net for users not having strict static type
            # checking.
            retval = method.exit_mode()  # type: ignore[func-returns-value]
            if retval is not None:
                raise ValueError("exit_mode returned a value other than None!")
        except Exception as e:
            raise RuntimeError(errortxt + "Original error: " + str(e))

    if heartbeat_stopped is not True:
        raise RuntimeError(
            f"The heartbeat of {method.__class__.__name__} ({method.name}) could not "
            "be stopped! Suggesting submitting a bug report and rebooting for "
            "clearing the mode. "
        )

    if method.dbus_adapter:
        method.dbus_adapter.close_connections()


def get_platform_supported(method: Method, platform: PlatformName) -> bool:
    """Checks if method is supported by the platform

    Parameters
    ----------
    method: Method
        The method which platform support to check.
    platform:
        The platform to check against.

    Returns
    -------
    is_supported: bool
        If True, the platform is supported. Otherwise, False.
    """
    return platform in method.supported_platforms


def caniuse_fails(method: Method) -> tuple[bool, str]:
    """Check if the requirements of a Method are met or not.

    Returns
    -------
    (fail, message): (bool, str)
        If Method.caniuse() return True or None, the requirements check does
        not fail. In this case, return(False, '')

        If Method.caniuse() return False, or a string, the requirements check
        fails, and this function returns (True, message), where message is
        either the string returned by .caniuse() or emptry string.
    """

    try:
        canuse = method.caniuse()
    except Exception as exc:
        return True, str(exc)

    fail = False if (canuse is True or canuse is None) else True
    message = "" if canuse in {True, False, None} else str(canuse)

    return fail, message


def try_enter_and_heartbeat(method: Method) -> Tuple[bool, str, Optional[dt.datetime]]:
    """Try to use a Method to to activate a mode. First, with
    method.enter_mode(), and then with the method.heartbeat()

    Returns
    -------
    success, err_message, heartbeat_call_time
        A three-tuple, where success is boolean and True if activating the mode
        with the method was successful, otherwise False. The err_message is a
        string which may be non-empty only when success is False. The
        heartbeat_call_time is the datetime (in UTC) just before calling the
        method.heartbeat().

    Raises
    ------
    RunTimeError: In the rare edge case where the `method` has both,
    enter_mode() and heartbeat() defined, and the enter_mode() succeeds but the
    heartbeat() fails, which causes exit_mode() to be called, and if this
    exit_mode() also fails (as this leaves system uncertain state). All other
    Exceptions are handled (returning success=False).

    Detailed explanation
    --------------------
    These are the three possible statuses from attempts to use either
    enter_mode() or heartbeat():

    M: Missing implementation
    F: Failed attempt
    S: Succesful attempt

    There are total of 7 different outcomes (3*3 possibilities, minus two from
    not checking heartbeat if enter_mode fails), marked as
    {enter_mode_outcome}{heartbeat_outcome}; MS means enter_mode() was missing
    implementation and using heartbeat() was successful.

    All the possible combinations which may occur are

    outcome    What to do
    -------    ---------------------------------------------------------
     1)  F*    Return Fail + enter_mode error message

     2)  MM    Raise Exception -- the Method is faulty.
     3)  MF    Return Fail + heartbeat error message
     4)  MS    Return Success + heartbeat time

     5)  SM    Return Success
     6)  SF    Return Fail + heartbeat error message + call exit_mode()
     7)  SS    Return Success + heartbeat time

    """
    enter_outcome, enter_errmessage = _try_enter_mode(method)

    if enter_outcome == MethodOutcome.FAILURE:  # 1) F*
        return False, enter_errmessage, None

    hb_outcome, hb_errmessage, hb_calltime = _try_heartbeat(method)

    method_name = f"Method {method.__class__.__name__} ({method.name})"
    if enter_outcome == MethodOutcome.NOT_IMPLEMENTED:
        if hb_outcome == MethodOutcome.NOT_IMPLEMENTED:
            errmsg = (
                f"{method_name} is not properly defined! Missing implementation for "
                "both, enter_mode() and heartbeat()!"
            )
            return False, errmsg, None  # 2) MM
        elif hb_outcome == MethodOutcome.FAILURE:
            return False, hb_errmessage, None  # 3) MF
        elif hb_outcome == MethodOutcome.SUCCESS:
            return True, "", hb_calltime  # 4) MS

    elif enter_outcome == MethodOutcome.SUCCESS:
        if hb_outcome == MethodOutcome.NOT_IMPLEMENTED:  # 5) SM
            return True, "", None
        elif hb_outcome == MethodOutcome.FAILURE:  # 6) SF
            _rollback_with_exit(method)
            return False, hb_errmessage, None
        elif hb_outcome == MethodOutcome.SUCCESS:  # 7) SS
            return True, "", hb_calltime

    raise RuntimeError(  # pragma: no cover
        "Should never end up here. Check the return values for the enter_mode() and "
        f"heartbeat() of the {method_name}"
    )


def _try_enter_mode(method: Method) -> Tuple[MethodOutcome, str]:
    """Calls the method.enter_mode(). This function catches any possible
    Exceptions during the call."""

    if not has_enter(method):
        return MethodOutcome.NOT_IMPLEMENTED, ""

    outcome, err_message = _try_method_call(method, "enter_mode")

    return outcome, err_message


def _try_heartbeat(method: Method) -> Tuple[MethodOutcome, str, Optional[dt.datetime]]:
    """Calls the method.heartbeat(). This function catches any possible
    Exceptions during the call.

    Returns
    -------
    heartbeat_call_time: dt.datetime
        The UTC time just before the method.heartbeat() was called.
    """
    if not has_heartbeat(method):
        return MethodOutcome.NOT_IMPLEMENTED, "", None

    heartbeat_call_time = dt.datetime.now(dt.timezone.utc)
    outcome, err_message = _try_method_call(method, "heartbeat")

    return outcome, err_message, heartbeat_call_time


def _try_method_call(method: Method, mthdname: str) -> Tuple[MethodOutcome, str]:
    try:
        method_to_call = getattr(method, mthdname)
        retval = method_to_call()
        if retval is not None:
            raise ValueError(
                f"The {mthdname} of {method.__class__.__name__} ({method.name}) "
                f"returned an unsupported value {retval}. The only accepted return "
                "value is None"
            )
        outcome = MethodOutcome.SUCCESS
        err_message = ""
    except Exception as exc:
        err_message = repr(exc)
        outcome = MethodOutcome.FAILURE
    return outcome, err_message


def _rollback_with_exit(method: Method) -> None:
    """Roll back entering a mode by exiting it.

    Raises
    ------
    RuntimeError, if exit_mode fails (returns something else than None)

    Notes
    -----
    This function has the side effect of executing the calls in the
    method.exit_mode.
    """
    if not has_exit(method):
        # Nothing to exit from.
        return

    try:
        # The Method.exit_mode() *should* always return None. However, it
        # is not possible to control user created Methods implementation,
        # so this is a safety net for users not having strict static type
        # checking.
        exit_outcome = method.exit_mode()  # type: ignore[func-returns-value]
        if exit_outcome is not None:
            raise ValueError("exit_method did not return None")
    except Exception as exc:
        raise RuntimeError(
            f"Entered {method.__class__.__name__} ({method.name}) but could not exit!"
            + f" Original error: {str(exc)}"
        ) from exc


def has_enter(method: Method) -> bool:
    return type(method).enter_mode is not Method.enter_mode


def has_exit(method: Method) -> bool:
    return type(method).exit_mode is not Method.exit_mode


def has_heartbeat(method: Method) -> bool:
    return type(method).heartbeat is not Method.heartbeat
