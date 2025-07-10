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
from textwrap import dedent, fill, wrap

from wakepy import ModeExit
from wakepy.core.constants import ModeName
from wakepy.core.mode import Mode
from wakepy.core.platform import CURRENT_PLATFORM, get_platform_debug_info, is_windows

if typing.TYPE_CHECKING:
    from typing import List, Tuple

    from wakepy import ActivationResult

WAKEPY_LOGO_TEMPLATE = r"""                         _
                        | |
        __      __ __ _ | | __ ___  _ __   _   _
        \ \ /\ / // _` || |/ // _ \| '_ \ | | | |
         \ V  V /| (_| ||   <|  __/| |_) || |_| |
          \_/\_/  \__,_||_|\_\\___|| .__/  \__, |
       {version_string}| |      __/ |
                                   |_|     |___/ """

WAKEPY_INFO_UNICODE_TEMPLATE = (
    WAKEPY_LOGO_TEMPLATE
    + """
 ┏━━ Mode: {wakepy_mode} {header_bars}━┓
 ┃                                                      ┃
 ┃  [{no_auto_suspend}] Programs keep running                           ┃
 ┃  [{presentation_mode}] Display kept on, screenlock disabled            ┃
 ┃                                                      ┃
 ┃   Method: {wakepy_method} {method_spacing}┃
 ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"""
)

WAKEPY_INFO_ASCII_TEMPLATE = (
    WAKEPY_LOGO_TEMPLATE
    + """
 ┏━━ Mode: {wakepy_mode} {header_bars}━┓
 ┃                                                      ┃
 ┃  [{no_auto_suspend}] Programs keep running                           ┃
 ┃  [{presentation_mode}] Display kept on, screenlock disabled            ┃
 ┃                                                      ┃
 ┃   Method: {wakepy_method} {method_spacing}┃
 ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"""
)


def main() -> None:
    mode_name, deprecations = parse_arguments(sys.argv[1:])
    mode = Mode.from_name(mode_name, on_fail=handle_activation_error)

    ascii_only = get_should_use_ascii_only()

    # print the deprecations _after_ the startup text to make them more visible

    with mode:
        if not mode.active:
            raise ModeExit

        print(get_wakepy_cli_info(mode, ascii_only, deprecations))
        wait_until_keyboardinterrupt(ascii_only)

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
) -> Tuple[ModeName, str]:
    """Parses arguments from sys.argv and returns the name of the mode and
    deprecation message, if any."""

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

    return mode, "\n".join(deprecations) if deprecations else ""


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


def get_wakepy_cli_info(mode: Mode, ascii_only: bool, deprecations: str) -> str:
    from wakepy import __version__

    template = (
        WAKEPY_INFO_ASCII_TEMPLATE if ascii_only else WAKEPY_INFO_UNICODE_TEMPLATE
    )

    mode_name_max_length = 43
    method_name_max_length = 42
    mode_name = mode.name or "(unknown mode)"
    mode_name = mode_name[:mode_name_max_length]
    header_bars = "━" * (mode_name_max_length - len(mode_name))

    method_name = mode.active_method or "(no method)"
    method_name = method_name[:method_name_max_length]
    method_spacing = " " * (method_name_max_length - len(method_name))

    presentation_mode_symbol = _get_success_or_fail_symbol(
        mode_name == ModeName.KEEP_PRESENTING, ascii_only
    )

    cli_text = template.strip("\n").format(
        version_string=f"{'  v.'+__version__[:24]: <28}",
        wakepy_mode=mode_name,
        header_bars=header_bars,
        no_auto_suspend=_get_success_or_fail_symbol(True, ascii_only),
        presentation_mode=presentation_mode_symbol,
        wakepy_method=method_name,
        method_spacing=method_spacing,
    )
    if deprecations:
        cli_text += (
            "\n\n" + "\n".join(wrap("DEPRECATION NOTICE: " + deprecations, 66)) + "\n"
        )
    return cli_text


def _get_success_or_fail_symbol(success: bool, ascii_only: bool) -> str:
    if success:
        symbol = "x" if ascii_only else "✔"
    else:
        symbol = " "
    return symbol


def wait_until_keyboardinterrupt(ascii_only: bool) -> None:
    spinner_symbols = get_spinner_symbols(ascii_only)
    width = 32 if ascii_only else 31
    try:
        for spinner_symbol in itertools.cycle(spinner_symbols):  # pragma: no branch
            print(
                "\r " + " " + spinner_symbol + " " * width + r"[Press Ctrl+C to exit] ",
                end="",
            )
            time.sleep(0.8)
    except KeyboardInterrupt:
        pass


def get_should_use_ascii_only() -> bool:
    if (
        is_windows(CURRENT_PLATFORM)
        and platform.python_implementation().lower() == "pypy"
    ):
        # Windows + PyPy combination does not support unicode well, at least
        # yet at version 7.3.17. See:
        # https://github.com/pypy/pypy/issues/3890
        # https://github.com/fohrloop/wakepy/issues/274#issuecomment-2363293422
        return True
    return False


def get_spinner_symbols(ascii_only: bool = False) -> list[str]:
    if ascii_only:
        return ["|", "/", "-", "\\"]
    return ["⢎⡰", "⢎⡡", "⢎⡑", "⢎⠱", "⠎⡱", "⢊⡱", "⢌⡱", "⢆⡱"]


if __name__ == "__main__":
    main()  # pragma: no cover
