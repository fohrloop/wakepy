import ctypes
import enum

from wakepy.core import (
    Method,
    ModeName,
    PlatformName,
)

# Different flags for WindowsSetThreadExecutionState
#
# "Informs the system that the state being set should remain in effect until the
# next call that uses ES_CONTINUOUS and one of the other state flags is
# cleared."[1]
ES_CONTINUOUS = 0x80000000
# "Forces the system to be in the working state by resetting the system idle
# timer."[1] Keeps CPU awake, but does not prevent screen lock
ES_SYSTEM_REQUIRED = 0x00000001
# "Forces the display to be on by resetting the display idle timer."[1]
# Prevents automatic screen lock.
ES_DISPLAY_REQUIRED = 0x00000002


class Flags(enum.IntFlag):
    KEEP_RUNNING = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    KEEP_PRESENTING = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    RELEASE = ES_CONTINUOUS


class WindowsSetThreadExecutionState(Method):
    """This is a method which calls the SetThreadExecutionState function from
    the kernel32.dll. The SetThreadExecutionState informs "the system that it
    is in use, thereby preventing the system from entering sleep or turning off
    the display while the application is running"[1] (depending on the used
    flags)."""

    # The docs say that supports Windows XP and above (client) or Windows
    # Server 2003 and above (server)
    supported_platforms = (PlatformName.WINDOWS,)

    def enter_mode(self):
        # Sets the flags until ES_CONTINUOUS is called or until the thread
        # which called this dies.
        ctypes.windll.kernel32.SetThreadExecutionState(self.flags.value)

    def exit_mode(self):
        ctypes.windll.kernel32.SetThreadExecutionState(Flags.RELEASE.value)


class WindowsKeepRunning(WindowsSetThreadExecutionState):
    mode = ModeName.KEEP_RUNNING
    flags = Flags.KEEP_RUNNING
    name = "SetThreadExecutionState"


class WindowsKeepPresenting(WindowsSetThreadExecutionState):
    mode = ModeName.KEEP_PRESENTING
    flags = Flags.KEEP_PRESENTING
    name = "SetThreadExecutionState"


"""
References
-----------
[1] https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
"""
