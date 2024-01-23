"""This module defines the CLI for wakepy

This is called either with

    python -m wakepy [args]

or using the executable

    wakepy [args]
"""
import argparse
import time
from typing import Dict
import sys

from wakepy.core.constants import ModeName
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


def main():
    kwargs = parse_arguments(sys.argv)
    mode = create_mode(**kwargs)
    with mode:
        if not mode.active:
            raise RuntimeError("Could not activate")
        print_on_start(mode=kwargs["modename"])
        wait_until_keyboardinterrupt()

    print("\nExited.")


def parse_arguments(args: list[str]) -> Dict[str, ModeName]:
    """Parses arguments from sys.argv and returns kwargs for"""
    args = _get_argparser().parse_args(args)

    n_flags_selected = sum((args.keep_running, args.presentation))

    if n_flags_selected > 1:
        raise ValueError('You may only select one of the modes! See: "wakepy -h"')

    if n_flags_selected == 0:
        # The default action, if nothing is selected, is "keep running"
        mode = ModeName.KEEP_RUNNING
    else:
        if args.keep_running:
            mode = ModeName.KEEP_RUNNING
        else:
            assert args.presentation
            mode = ModeName.KEEP_PRESENTING

    return dict(modename=mode)


def _get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wakepy",
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog,
            # makes more space for the "options" area on the left
            max_help_position=27,
        ),
    )

    common_kwargs = dict(action="store_true", default=False)

    parser.add_argument(
        "-k",
        "--keep-running",
        help=(
            "Keep programs running; inhibit automatic idle timer based sleep / suspend. "
            "If a screen lock (or a screen saver) with a password is enabled, your "
            "system *may* still lock the session automatically. You may, and probably "
            "should, lock the session manually. Locking the workstation does not stop "
            "programs from executing. This is used as the default if no modes are "
            "selected."
        ),
        **common_kwargs,
    )

    parser.add_argument(
        "-p",
        "--presentation",
        help=(
            "Presentation mode; inhibit automatic idle timer based sleep, screensaver, "
            "screenlock and display power management."
        ),
        **common_kwargs,
    )

    return parser


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


if __name__ == "__main__":
    main()
