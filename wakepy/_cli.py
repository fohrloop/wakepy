"""This module defines the CLI for wakepy

This module provides:

start() 
- Function that starts a "keepawake". Keeps the computer
  awake. Exit with Ctrl-C.
"""

import time
import warnings
from contextlib import ExitStack

from wakepy import keep
from wakepy._system import CURRENT_SYSTEM, SystemName

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
            "behaviour at https://github.com/np-8/wakepy"
        )
    print(" ")


def start(
    keep_running: bool = False,
    presentation_mode: bool = False,
    deprecation_warning: bool = False,
):
    """
    Start the keep-awake. During keep-awake, the CPU is not allowed to
    go to sleep automatically until the CTRL+C is pressed.
    """

    real_successes = dict()
    with ExitStack() as stack:
        if keep_running:
            m = stack.enter_context(keep.running())
            real_successes["keep_running"] = m.real_success
        if presentation_mode:
            m = stack.enter_context(keep.presenting())
            real_successes["presentation_mode"] = m.real_success

        # A quick fix (Fix this better in next release)
        # On linux, D-Bus methods for keep_running use presentation_mode.
        if CURRENT_SYSTEM == SystemName.LINUX and real_successes.get("keep_running"):
            real_successes["presentation_mode"] = True

        print_on_start(**real_successes)

        if deprecation_warning:
            warnings.warn(
                "The -s/--keep-screen-awake option is deprecated and will be removed in"
                " a future release! Use the -p/--presentation flag, instead!\n"
            )
        wait_until_keyboardinterrupt()

    print("\nExited.")
