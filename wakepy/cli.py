"""This module defines the CLI for wakepy

This module provides:

start() 
- Function that starts a "keepawake". Keeps the computer
  awake. Exit with Ctrl-C.
"""

import time
import warnings

from wakepy.core.constants import PlatformName, ModeName
from wakepy.core.platform import CURRENT_PLATFORM
from wakepy.core import Mode
from wakepy.core.mode import create_mode

WAKEPY_TEXT_TEMPLATE = r"""                  _                       
                 | |                      
 __      __ __ _ | | __ ___  _ __   _   _ 
 \ \ /\ / // _` || |/ // _ \| '_ \ | | | |
  \ V  V /| (_| ||   <|  __/| |_) || |_| |
   \_/\_/  \__,_||_|\_\\___|| .__/  \__, |
{VERSION_STRING}        | |      __/ |
                            |_|     |___/ """

WAKEPY_TICKBOXES_TEMPLATE = """
 [{no_auto_suspend}] System will continue running programs
 [{presentation_mode}] Presentation mode is on 

""".strip(
    "\n"
)


def wakepy_text():
    from wakepy import __version__

    return WAKEPY_TEXT_TEMPLATE.format(VERSION_STRING=f"{'  v.'+__version__: <20}")


def create_wakepy_opts_text(keep_running: bool, presentation_mode: bool) -> str:
    opts = dict(
        no_auto_suspend=keep_running or presentation_mode,
        presentation_mode=presentation_mode,
    )
    option_to_string = {True: "x", False: " ", None: "?"}

    return WAKEPY_TICKBOXES_TEMPLATE.format(
        **{key: option_to_string.get(val) for key, val in opts.items()}
    )


def wait_until_keyboardinterrupt():
    spinning_chars = ["|", "/", "-", "\\"]
    try:
        while True:
            for i in range(0, 4):
                print("\r" + spinning_chars[i] + r" [Press Ctrl+C to exit]", end="")
                time.sleep(1)
    except KeyboardInterrupt:
        pass


def print_on_start(keep_running: bool = False, presentation_mode: bool = False):
    """
    Parameters
    ----------
    presentation_mode: bool
        The option to select if screen is to be kept on.
    """

    wakepy_opts_text = create_wakepy_opts_text(
        keep_running=keep_running, presentation_mode=presentation_mode
    )

    print(wakepy_text())
    print(wakepy_opts_text)
    if "[?]" in wakepy_opts_text:
        print(
            """\nThe reason you are seeing "[?]" is because the feature is untested """
            "on your platform.\nIf you wish, you can contribute and inform the "
            "behaviour at https://github.com/fohrloop/wakepy"
        )
    print(" ")


def start(
    modename: ModeName,
):
    mode = create_mode(modename)
    with mode:
        if not mode.active:
            raise RuntimeError(f"Could not activate")

        print_on_start(**real_successes)
        wait_until_keyboardinterrupt()

    print("\nExited.")
