import ctypes
import enum
from abc import ABC, abstractmethod

from wakepy.core import Method, ModeName, PlatformName

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
    the kernel32.dll. The SetThreadExecutionState informs the system that it
    is in use preventing the system from entering sleep or turning off
    the display while the application is running" (depending on the used
    flags)."""

    # The docs say that supports Windows XP and above (client) or Windows
    # Server 2003 and above (server)
    supported_platforms = (PlatformName.WINDOWS,)

    def enter_mode(self) -> None:
        # Sets the flags until Flags.RELEASE is used or until the thread
        # which called this dies.
        self._call_set_thread_execution_state(self.flags.value)

    def exit_mode(self) -> None:
        self._call_set_thread_execution_state(Flags.RELEASE.value)

    def _call_set_thread_execution_state(self, flags: int) -> None:
        try:
            ctypes.windll.kernel32.SetThreadExecutionState(flags)  # type: ignore[attr-defined,unused-ignore]
        except AttributeError as exc:
            raise RuntimeError("Could not use kernel32.dll!") from exc

    @property
    @abstractmethod
    def flags(self) -> Flags: ...


class WindowsKeepRunning(WindowsSetThreadExecutionState):
    mode_name = ModeName.KEEP_RUNNING
    flags = Flags.KEEP_RUNNING
    name = "SetThreadExecutionState"


class WindowsKeepPresenting(WindowsSetThreadExecutionState):
    mode_name = ModeName.KEEP_PRESENTING
    flags = Flags.KEEP_PRESENTING
    name = "SetThreadExecutionState"
