"""This module defines the CLI for wakepy

This is called either with

    python -m wakepy [args]

or using the executable

    wakepy [args]
"""
from __future__ import annotations

import argparse
import itertools
import sys
import time
import typing

from wakepy.core.constants import ModeName
from wakepy.core.mode import create_mode

if typing.TYPE_CHECKING:
    from typing import List

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
"""


def main():
    modename = parse_arguments(sys.argv[1:])
    mode = create_mode(modename=modename)
    with mode:
        if not mode.active:
            raise RuntimeError("Could not activate")
        print(get_startup_text(mode=modename))
        wait_until_keyboardinterrupt()

    print("\nExited.")


def parse_arguments(
    sysargs: List[str],
) -> ModeName:
    """Parses arguments from sys.argv and returns kwargs for"""

    args = _get_argparser().parse_args(sysargs)

    n_flags_selected = sum((args.keep_running, args.presentation))

    if n_flags_selected > 1:
        raise ValueError('You may only select one of the modes! See: "wakepy -h"')

    if args.keep_running or n_flags_selected == 0:
        # The default action, if nothing is selected, is "keep running"
        mode = ModeName.KEEP_RUNNING
    else:
        assert args.presentation
        mode = ModeName.KEEP_PRESENTING

    return mode


def _get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wakepy",
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog,
            # makes more space for the "options" area on the left
            max_help_position=27,
        ),
    )

    parser.add_argument(
        "-k",
        "--keep-running",
        help=(
            "Keep programs running; inhibit automatic idle timer based sleep / "
            "suspend. If a screen lock (or a screen saver) with a password is enabled, "
            "your system *may* still lock the session automatically. You may, and "
            "probably should, lock the session manually. Locking the workstation does "
            "not stop programs from executing. This is used as the default if no modes "
            "are selected."
        ),
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-p",
        "--presentation",
        help=(
            "Presentation mode; inhibit automatic idle timer based sleep, screensaver, "
            "screenlock and display power management."
        ),
        action="store_true",
        default=False,
    )

    return parser


def get_startup_text(mode: ModeName) -> str:
    from wakepy import __version__

    wakepy_text = WAKEPY_TEXT_TEMPLATE.format(
        VERSION_STRING=f"{'  v.'+__version__: <20}"
    )
    options_txt = WAKEPY_TICKBOXES_TEMPLATE.strip("\n").format(
        no_auto_suspend="x",
        presentation_mode="x" if mode == ModeName.KEEP_PRESENTING else " ",
    )
    return "\n".join((wakepy_text, options_txt)) + "\n"


def wait_until_keyboardinterrupt():
    spinning_chars = ["|", "/", "-", "\\"]
    try:
        for char in itertools.cycle(spinning_chars):  # pragma: no branch
            print("\r" + char + r" [Press Ctrl+C to exit]", end="")
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()  # pragma: no cover
