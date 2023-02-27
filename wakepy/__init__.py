"""This module provides 

start() 
- Function that starts a "keepawake". Keeps the computer
  awake. Exit with Ctrl-C.

set_keepawake()
unset_keepawake()
- The lower level functions that can be used in any script to
   set or unset the keepawake.

keepawake()
- A context manager that sets and unsets keepawake.
"""
import enum
import platform
import time
from contextlib import contextmanager

from wakepy._common import print_on_start

__version__ = "0.6.0"
CURRENT_SYSTEM = platform.system().lower()


class System(str, enum.Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"


if CURRENT_SYSTEM == System.WINDOWS:
    from ._win import set_keepawake, unset_keepawake
elif CURRENT_SYSTEM == System.LINUX:
    from ._linux import set_keepawake, unset_keepawake
elif CURRENT_SYSTEM == System.DARWIN:
    from ._darwin import set_keepawake, unset_keepawake
else:
    raise NotImplementedError(
        f"wakepy has not yet a {CURRENT_SYSTEM} implementation. "
        "Pull requests welcome: https://github.com/np-8/wakepy"
    )


@contextmanager
def keepawake(*args, **kwargs):
    set_keepawake(*args, **kwargs)

    try:
        yield
    finally:
        unset_keepawake()


def wait_until_keyboardinterrupt():
    SPINNING_CHARS = ["|", "/", "-", "\\"]
    try:
        while True:
            for i in range(0, 4):
                print("\r" + SPINNING_CHARS[i] + r" [Press Ctrl+C to exit]", end="")
                time.sleep(1)
    except KeyboardInterrupt:
        pass


def start(keep_screen_awake=False):
    """
    Start the keep-awake. During keep-awake, the CPU is not allowed to
    go to sleep automatically until the CTRL+C is pressed.

    Parameters
    -----------
    keep_screen_awake: bool
        If True, keeps also the screen awake.
    """

    with keepawake(keep_screen_awake=keep_screen_awake):
        print_on_start(keep_screen_awake=keep_screen_awake)
        wait_until_keyboardinterrupt()

    print("\nExited.")
