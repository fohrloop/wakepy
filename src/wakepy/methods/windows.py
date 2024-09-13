from __future__ import annotations

import ctypes
import enum
import logging
import threading
import typing
from abc import ABC, abstractmethod
from queue import Queue
from threading import Event, Thread

from wakepy.core import Method, ModeName, PlatformType

logger = logging.getLogger(__name__)

# Different flags for WindowsSetThreadExecutionState
# See: https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002


class Flags(enum.IntFlag):
    KEEP_RUNNING = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    KEEP_PRESENTING = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    RELEASE = ES_CONTINUOUS


class WindowsSetThreadExecutionState(Method, ABC):
    """This is a method which calls the SetThreadExecutionState function from
    the kernel32.dll. The SetThreadExecutionState informs the system that it is
    in use preventing the system from entering sleep or turning off the display
    while the application is running" (depending on the used flags)."""

    # The SetThreadExecutionState docs say that it supports Windows XP and
    # above (client) or Windows Server 2003 and above (server)
    supported_platforms = (PlatformType.WINDOWS,)
    _wait_timeout = 5  # seconds
    """timeout for calls like queue.get() and thread.join() which could
    otherwise block execution indefinitely."""

    @property
    @abstractmethod
    def flags(self) -> Flags: ...

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._inhibiting_thread: Thread | None = None
        self._release = Event()
        self._queue_from_thread: Queue[int | Exception] = Queue()

    def enter_mode(self) -> None:
        # Because the ExecutionState flags are global per each thread, and
        # multiple wakepy modes might be activated simultaneously, we must
        # put all the SetThreadExecutionState inhibitor flags into separate
        # threads. See: https://github.com/fohrloop/wakepy/issues/167
        self._inhibiting_thread = threading.Thread(
            target=_inhibit_until_released,
            args=(self.flags, self._release, self._queue_from_thread),
        )
        self._inhibiting_thread.start()
        self._check_thread_response()

    def exit_mode(self) -> None:
        self._release.set()
        self._check_thread_response()
        if self._inhibiting_thread:
            self._inhibiting_thread.join(timeout=self._wait_timeout)
        self._inhibiting_thread = None

    def _check_thread_response(self) -> None:
        """Waits a message from the inhibitor thread queue. It should be an
        integer representing the previous thread execution state flags. If
        it's not, raises an Exception. Re-raises any Exceptions put into the
        queue.
        """
        res = self._queue_from_thread.get(timeout=self._wait_timeout)

        if isinstance(res, int):
            logger.debug("The previous flags were %s (%s)", res, Flags(res))
            return  # success
        elif isinstance(res, Exception):
            # re-raise any exceptions occurred in the thread
            raise res
        raise RuntimeError(f"Unknown result type: {type(res)} ({res})")


def _inhibit_until_released(
    flags: Flags, exit_event: Event, queue: Queue[int | Exception]
) -> None:
    _call_and_put_result_in_queue(flags.value, queue)
    exit_event.wait(_release_event_timeout)
    _call_and_put_result_in_queue(Flags.RELEASE.value, queue)


_release_event_timeout: int | float | None = None
"""Timeout for the release events (to stop a inhibit thread). None means
wait indefinitely. This variable exists for tests (edit this to make tests not
to wait forever in case of errors).
"""


def _call_and_put_result_in_queue(flags: int, queue: Queue[int | Exception]) -> None:
    try:
        prev_flags = _call_set_thread_execution_state(flags)
        queue.put(prev_flags)
    except Exception as exc:
        queue.put(exc)


def _call_set_thread_execution_state(flags: int) -> int:
    """Call the SetThreadExecutionState with the given flags.

    Parameters
    ----------
    flags: int
        The flags to set. For example, KEEP_PRESENTING state is 2147483651
        and the RELEASE flags is 2147483648.

    Returns
    -------
    int:
        Flags value of the previous thread execution state as returned from the
        SetThreadExecutionState call.

    Raises
    ------
    RuntimeError:
        If the kernel32.dll is not found or if the SetThreadExecutionState
        returns NULL (0), indicating an error.
    """
    try:
        # This sets the return type to be unsigned 32-bit integer. Otherwise it
        # will be a signed 32-bit integer which is overflown. So for example
        # instead of returning 2147483649 it would return -2147483647.
        ctypes.windll.kernel32.SetThreadExecutionState.restype = ctypes.c_uint32  # type: ignore[attr-defined,unused-ignore]
        logger.debug(
            "Calling SetThreadExecutionState with flags: %s (%s)", flags, Flags(flags)
        )
        # The return value will be 0 in case of error, and the value of the
        # previous thread execution state otherwise.
        retval = ctypes.windll.kernel32.SetThreadExecutionState(flags)  # type: ignore[attr-defined,unused-ignore]
    except AttributeError as exc:
        raise RuntimeError("Could not use kernel32.dll!") from exc

    if retval == 0:
        raise RuntimeError("SetThreadExecutionState returned NULL")

    return typing.cast(int, retval)


class WindowsKeepRunning(WindowsSetThreadExecutionState):
    mode_name = ModeName.KEEP_RUNNING
    flags = Flags.KEEP_RUNNING
    name = "SetThreadExecutionState"


class WindowsKeepPresenting(WindowsSetThreadExecutionState):
    mode_name = ModeName.KEEP_PRESENTING
    flags = Flags.KEEP_PRESENTING
    name = "SetThreadExecutionState"
