import ctypes

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
# See:
# https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate


def set_keepawake(keep_screen_awake=False):
    """
    Set the keep-awake. During keep-awake, the CPU is not allowed to go to
    sleep automatically until the `unset_keepawake` is called*.

    Parameters
    -----------
    keep_screen_awake: bool
        If True, keeps also the screen awake.

    TIP: You may check the flags by running `powercfg -requests` in an elevated
    PowerShell.

    * Or, if SetThreadExecutionState is called in another way with a flag that
      clears ES_SYSTEM_REQUIRED.
    * Or, if the Thread which called `set_keepawake` dies.

    """
    flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    if keep_screen_awake:
        flags |= ES_DISPLAY_REQUIRED

    ctypes.windll.kernel32.SetThreadExecutionState(flags)


def unset_keepawake():
    """
    Remove all flags set with set_keepawake. Can only change
    flags set by the same thread.

    TIP: You may check the flags by running `powercfg -requests` in an elevated
    PowerShell.
    """
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
