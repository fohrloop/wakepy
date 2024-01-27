import enum
from abc import ABC, abstractmethod
from subprocess import Popen, PIPE
from typing import List

from wakepy.core import DbusAdapter, Method, ModeName, PlatformName

class Flags(enum.StrEnum):
    KEEP_RUNNING = "$ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED"
    KEEP_PRESENTING = "$ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_DISPLAY_REQUIRED"
    RELEASE = "$ES_CONTINUOUS"


class WslSetThreadExecutionState(Method, ABC):
    """This is a method which calls the SetThreadExecutionState function from
    the kernel32.dll using PowerShell.exe. The SetThreadExecutionState informs the system that it
    is in use preventing the system from entering sleep or turning off
    the display while the application is running" (depending on the used
    flags)."""

    # This should support Windows 7 and above out of the box.  Windows XP and above if PowerShell 2 is installed.
    supported_platforms = (PlatformName.WSL,)

    def __init__(self, dbus_adapter: DbusAdapter | None = None):
        self._powershell: Popen = None

        super().__init__(dbus_adapter)

    def enter_mode(self):
        self._powershell = Popen(["powershell.exe"], stdout=PIPE, stderr=None, stdin=PIPE, universal_newlines=True)

        # C# Code to allow PowerShell to call SetThreadExecutionState
        code = """$code = @'
[DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern void SetThreadExecutionState(uint esFlags);
'@""".strip().split("\n")
        
        # Write the code line, by line
        self._write(*code)
        # Write a blank line to complete the code block.
        self._write("")

        # Add the code above to the PowerShell Context.
        self._write("$ste = Add-Type -MemberDefinition $code -Name System -Namespace Win32 -PassThru")

        # Different flags for WindowsSetThreadExecutionState
        # See: https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
        self._write("$ES_CONTINUOUS = [uint32]\"0x80000000\"")
        self._write("$ES_SYSTEM_REQUIRED = [uint32]\"0x00000001\"")
        self._write("$ES_DISPLAY_REQUIRED = [uint32]\"0x00000002\"")

        # Force a flush to make sure everything executes.
        self._powershell.stdin.flush()

        # Sets the flags until Flags.RELEASE is used or until the thread
        # which called this dies.
        self._call_set_thread_execution_state(self.flags.value)

    def exit_mode(self):
        self._call_set_thread_execution_state(Flags.RELEASE.value)
        self._write("exit")
        self._powershell.stdin.flush()

        self._powershell.terminate()

    def _call_set_thread_execution_state(self, flags: str):
        self._write(f"$ste::SetThreadExecutionState({flags})")

        # Tests the result of the SetThreadExecutionState.
        # Close PowerShell if we failed.  This is easy to test for.
        self._write("([System.Runtime.InteropServices.Marshal]::GetLastWin32Error() -eq 0) | Where-Object { $_ } | Foreach-Object { exit -1 }")

        # Force a flush to make sure everything executes.        
        self._powershell.stdin.flush()

        # If PowerShell closed, we failed.
        if self._powershell.poll() is not None:
            raise RuntimeError("Could not use PowerShell to control kernel32.dll!")

    def _write(self, *lines: List[str]):
        for line in lines:
            self._powershell.stdin.write(f"{line}\n")


    @property
    @abstractmethod
    def flags(self) -> Flags:
        ...


class WslKeepRunning(WslSetThreadExecutionState):
    mode = ModeName.KEEP_RUNNING
    flags = Flags.KEEP_RUNNING
    name = "PowerShell_SetThreadExecutionState"


class WslKeepPresenting(WslSetThreadExecutionState):
    mode = ModeName.KEEP_PRESENTING
    flags = Flags.KEEP_PRESENTING
    name = "PowerShell_SetThreadExecutionState"
