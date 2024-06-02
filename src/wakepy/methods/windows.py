from __future__ import annotations

import ctypes
import enum
import threading
import typing
from abc import ABC, abstractmethod
from queue import Queue
from threading import Event, Thread

from wakepy.core import Method, ModeName, PlatformName

if typing.TYPE_CHECKING:
    from typing import Optional

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
    supported_platforms = (PlatformName.WINDOWS,)
    _wait_timeout = 5  # seconds

    @property
    @abstractmethod
    def flags(self) -> Flags: ...

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._inhibiting_thread: Thread | None = None
        self._release = Event()
        self._queue_from_thread: Queue[Optional[Exception]] = Queue()

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
        """Waits a message from the inhibitor thread queue. If the item put
        into the queue is not None, raises an Exception. Re-raises any
        Exceptions put into the queue.
        """
        res = self._queue_from_thread.get(timeout=self._wait_timeout)

        if res is None:
            return  # success
        elif isinstance(res, Exception):
            # re-raise any exceptions occurred in the thread
            raise res
        raise RuntimeError(f"Unknown result type: {type(res)} ({res})")


def _inhibit_until_released(
    flags: Flags, exit_event: Event, queue: Queue[Optional[Exception]]
) -> None:
    # Sets the flags until Flags.RELEASE is used or until the thread
    # which called this dies.
    _call_and_put_result_in_queue(flags.value, queue)
    exit_event.wait()
    _call_and_put_result_in_queue(Flags.RELEASE.value, queue)


def _call_and_put_result_in_queue(
    flags: int, queue: Queue[Optional[Exception]]
) -> None:
    try:
        _call_set_thread_execution_state(flags)
        queue.put(None)
    except Exception as exc:
        queue.put(exc)


def _call_set_thread_execution_state(flags: int) -> None:
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(flags)  # type: ignore[attr-defined,unused-ignore]
    except AttributeError as exc:
        raise RuntimeError("Could not use kernel32.dll!") from exc


class WindowsKeepRunning(WindowsSetThreadExecutionState):
    mode_name = ModeName.KEEP_RUNNING
    flags = Flags.KEEP_RUNNING
    name = "SetThreadExecutionState"


class WindowsKeepPresenting(WindowsSetThreadExecutionState):
    mode_name = ModeName.KEEP_PRESENTING
    flags = Flags.KEEP_PRESENTING
    name = "SetThreadExecutionState"
