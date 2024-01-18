import ctypes

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


class WindowsSetThreadExecutionState(Method):
    """This is a method which calls the SetThreadExecutionState function from
    the kernel32.dll. The SetThreadExecutionState informs "the system that it
    is in use, thereby preventing the system from entering sleep or turning off
    the display while the application is running"[1] (depending on the used
    flags)."""

    name = "SetThreadExecutionState"

    # The docs say that supports Windows XP and above (client) or Windows
    # Server 2003 and above (server)
    supported_platforms = (PlatformName.WINDOWS,)

    def enter_mode(self):
        # Sets the flags until ES_CONTINUOUS is called or until the thread
        # which called this dies.
        ctypes.windll.kernel32.SetThreadExecutionState(self.flags)

    def exit_mode(self):
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)


class WindowsKeepRunning(WindowsSetThreadExecutionState):
    mode = ModeName.KEEP_RUNNING
    flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED


class WindowsKeepPresenting(WindowsSetThreadExecutionState):
    mode = ModeName.KEEP_PRESENTING
    flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED


"""
References
-----------
[1] https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
"""
