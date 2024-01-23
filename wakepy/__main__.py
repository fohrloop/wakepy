"""This module defines the CLI for wakepy

This is called either with

    python -m wakepy [args]

or using the executable

    wakepy [args]
"""
import argparse
import time
from typing import Dict

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


def get_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wakepy",
        formatter_class=lambda prog: argparse.HelpFormatter(
            prog,
            # makes more space for the "options" area on the left
            max_help_position=27,
        ),
    )

    def add_mode(short, long, help, default=False):
        parser.add_argument(
            short, long, help=help, action="store_true", default=default
        )

    add_mode(
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
    )

    add_mode(
        "-p",
        "--presentation",
        help=(
            "Presentation mode; inhibit automatic idle timer based sleep, screensaver, "
            "screenlock and display power management."
        ),
    )

    return parser


def parse_arguments(parser: argparse.ArgumentParser) -> Dict[str, bool]:
    args = parser.parse_args()

    if not any((args.keep_running, args.presentation, args.keep_screen_awake)):
        # The default action, if nothing is selected, is "keep running"
        args.keep_running = True

    return dict(
        keep_running=args.keep_running,
        presentation_mode=args.presentation,
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
            raise RuntimeError("Could not activate")

        print_on_start(**real_successes)
        wait_until_keyboardinterrupt()

    print("\nExited.")


def main():
    parser = get_argparser()
    kwargs = parse_arguments(parser)
    start(**kwargs)


if __name__ == "__main__":
    main()
