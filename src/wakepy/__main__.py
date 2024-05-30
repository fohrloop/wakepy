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
from textwrap import dedent, fill

from wakepy import ModeExit
from wakepy.core.constants import ModeName
from wakepy.core.mode import Mode

if typing.TYPE_CHECKING:
    from typing import List

    from wakepy import ActivationResult

WAKEPY_TEXT_TEMPLATE = r"""                  _
                 | |
 __      __ __ _ | | __ ___  _ __   _   _
 \ \ /\ / // _` || |/ // _ \| '_ \ | | | |
  \ V  V /| (_| ||   <|  __/| |_) || |_| |
   \_/\_/  \__,_||_|\_\\___|| .__/  \__, |
{VERSION_STRING}| |      __/ |
                            |_|     |___/ """

WAKEPY_TICKBOXES_TEMPLATE = """
 [{no_auto_suspend}] System will continue running programs
 [{presentation_mode}] Presentation mode is on
"""


def main() -> None:
    mode_name = parse_arguments(sys.argv[1:])
    mode = Mode.from_name(mode_name, on_fail=handle_activation_error)
    print(get_startup_text(mode=mode_name))
    with mode:
        if not mode.active:
            raise ModeExit
        wait_until_keyboardinterrupt()

    if mode.activation_result and mode.activation_result.success:
        # If activation did not succeed, there is also no deactivation / exit.
        print("\n\nExited.")


def handle_activation_error(result: ActivationResult) -> None:
    print(_get_activation_error_text(result))


def _get_activation_error_text(result: ActivationResult) -> str:
    from wakepy import __version__

    error_text = f"""
    Wakepy could not activate the "{result.mode_name}" mode. This might occur because of a bug or because your current platform is not yet supported or your system is missing required software.

    Check if there is already a related issue in the issue tracker at https://github.com/fohrloop/wakepy/issues/ and if not, please create a new one.

    Include the following:
    - wakepy version: {__version__}
    - Mode: {result.mode_name}
    - Python version: {sys.version}
    - Operating system & version: [PLEASE FILL THIS]
    - Desktop Environment & version (if not default): [FILL OR REMOVE THIS LINE]
    - Additional details: [FILL OR REMOVE THIS LINE]

    Thank you!
    """  # noqa 501

    out = []
    for block in dedent(error_text.strip("\n")).split("\n"):
        out.append(fill(block, 80))

    return "\n".join(out)


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
        VERSION_STRING=f"{'  v.'+__version__: <28}"
    )
    options_txt = WAKEPY_TICKBOXES_TEMPLATE.strip("\n").format(
        no_auto_suspend="x",
        presentation_mode="x" if mode == ModeName.KEEP_PRESENTING else " ",
    )
    return "\n".join((wakepy_text, options_txt)) + "\n"


def wait_until_keyboardinterrupt() -> None:
    spinner_symbols = ["⢎⡰", "⢎⡡", "⢎⡑", "⢎⠱", "⠎⡱", "⢊⡱", "⢌⡱", "⢆⡱"]
    try:
        for spinner_symbol in itertools.cycle(spinner_symbols):  # pragma: no branch
            print("\r " + spinner_symbol + r" [Press Ctrl+C to exit] ", end="")
            time.sleep(0.8)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()  # pragma: no cover
