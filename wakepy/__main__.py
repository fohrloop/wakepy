"""Start wakepy keepawake with CLI

This is called either with

    python -m wakepy [args]

or using the executable

    wakepy [args]
"""
import argparse
from typing import Dict

from wakepy.cli import start


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


def main():
    parser = get_argparser()
    kwargs = parse_arguments(parser)
    start(**kwargs)


if __name__ == "__main__":
    main()
