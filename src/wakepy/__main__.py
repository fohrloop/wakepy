"""This module defines the CLI for wakepy

This is called either with

    python -m wakepy [args]

or using the executable

    wakepy [args]
"""

from __future__ import annotations

import argparse
import itertools
import platform
import sys
import time
import typing
from textwrap import dedent, fill

from wakepy import ModeExit
from wakepy.core.constants import ModeName
from wakepy.core.mode import Mode
from wakepy.core.platform import CURRENT_PLATFORM, get_platform_debug_info, is_windows

if typing.TYPE_CHECKING:
    from typing import List, Tuple

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
 [{presentation_mode}] Display is kept on and automatic screenlock disabled.
"""


def main() -> None:
    mode_name, deprecations = parse_arguments(sys.argv[1:])
    mode = Mode.from_name(mode_name, on_fail=handle_activation_error)
    print(get_startup_text(mode=mode_name))

    # print the deprecations _after_ the startup text to make them more visible
    for deprecation_msg in deprecations:
        print(deprecation_msg)  # pragma: no cover

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
    import textwrap

    from wakepy import __version__

    error_text = f"""
    Wakepy could not activate the "{result.mode_name}" mode. This might occur because of a bug or because your current platform is not yet supported or your system is missing required software.

    Check if there is already a related issue in the issue tracker at https://github.com/fohrloop/wakepy/issues/ and if not, please create a new one.

    Include the following:
    - wakepy version: {__version__}
    - Mode: {result.mode_name}
    - Python version: {sys.version}
    {textwrap.indent(get_platform_debug_info().strip(), ' '*4).strip()}
    - Additional details: [FILL OR REMOVE THIS LINE]

    Thank you!
    """  # noqa 501

    out = []
    for block in dedent(error_text.strip("\n")).split("\n"):
        out.append(fill(block, 80))

    return "\n".join(out)


def parse_arguments(
    sysargs: List[str],
) -> Tuple[ModeName, list[str]]:
    """Parses arguments from sys.argv and returns kwargs for"""

    args = _get_argparser().parse_args(sysargs)
    deprecations: list[str] = []

    if args.k:
        deprecations.append(
            "Using -k is deprecated in wakepy 0.10.0, and will be removed in a future "
            "release. Use -r/--keep-running, instead. "
            "Note that this is the default value so -r is optional.",
        )
    if args.presentation:
        deprecations.append(
            "Using --presentation is deprecated in wakepy 0.10.0, and will be removed "
            "in a future release. Use -p/--keep-presenting, instead. ",
        )

    # For the duration of deprecation, allow also the old flags
    keep_running = args.keep_running or args.k
    keep_presenting = args.keep_presenting or args.presentation

    n_flags_selected = sum((keep_running, keep_presenting))

    if n_flags_selected > 1:
        raise ValueError('You may only select one of the modes! See: "wakepy -h"')

    if keep_running or n_flags_selected == 0:
        # The default action, if nothing is selected, is "keep running"
        mode = ModeName.KEEP_RUNNING
    else:
        assert keep_presenting
        mode = ModeName.KEEP_PRESENTING

    return mode, deprecations


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
        "-r",
        "--keep-running",
        help=(
            "Keep programs running (DEFAULT); inhibit automatic idle timer based sleep "
            "/ suspend. If a screen lock (or a screen saver) with a password is "
            "enabled, your system *may* still lock the session automatically. You may, "
            "and probably should, lock the session manually. Locking the workstation "
            "does not stop programs from executing."
        ),
        action="store_true",
        default=False,
    )

    # old name for -r, --keep-running. Used during deprecation time
    parser.add_argument(
        "-k",
        help=argparse.SUPPRESS,
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-p",
        "--keep-presenting",
        help=(
            "Presentation mode; inhibit automatic idle timer based sleep, screensaver, "
            "screenlock and display power management."
        ),
        action="store_true",
        default=False,
    )

    # old name for -p, --keep-presenting. Used during deprecation time
    parser.add_argument(
        "--presentation",
        help=argparse.SUPPRESS,
        action="store_true",
        default=False,
    )

    return parser


def get_startup_text(mode: ModeName) -> str:
    from wakepy import __version__

    wakepy_text = WAKEPY_TEXT_TEMPLATE.format(
        VERSION_STRING=f"{'  v.'+__version__[:24]: <28}"
    )
    options_txt = WAKEPY_TICKBOXES_TEMPLATE.strip("\n").format(
        no_auto_suspend="x",
        presentation_mode="x" if mode == ModeName.KEEP_PRESENTING else " ",
    )
    return "\n".join((wakepy_text, options_txt)) + "\n"


def wait_until_keyboardinterrupt() -> None:
    spinner_symbols = get_spinner_symbols()
    try:
        for spinner_symbol in itertools.cycle(spinner_symbols):  # pragma: no branch
            print("\r " + spinner_symbol + r" [Press Ctrl+C to exit] ", end="")
            time.sleep(0.8)
    except KeyboardInterrupt:
        pass


def get_spinner_symbols() -> list[str]:

    if (
        is_windows(CURRENT_PLATFORM)
        and platform.python_implementation().lower() == "pypy"
    ):
        # Windows + PyPy combination does not support unicode well, at least
        # yet at version 7.3.17. See:
        # https://github.com/pypy/pypy/issues/3890
        # https://github.com/fohrloop/wakepy/issues/274#issuecomment-2363293422
        return ["|", "/", "-", "\\"]
    return ["⢎⡰", "⢎⡡", "⢎⡑", "⢎⠱", "⠎⡱", "⢊⡱", "⢌⡱", "⢆⡱"]


if __name__ == "__main__":
    main()  # pragma: no cover
