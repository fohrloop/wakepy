"""Start wakepy keepawake with CLI

This is called either with

    python -m wakepy [args]

or using the executable

    wakepy [args]
"""
import argparse

from wakepy._cli import start


def main():
    parser = argparse.ArgumentParser(
        prog="wakepy",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=27),
    )

    parser.add_argument(
        "-s",
        "--keep-screen-awake",
        help=(
            "Keep also the screen awake. "
            "On Linux, this flag is set on and cannot be disabled."
        ),
        action="store_true",
        default=False,
    )

    args = parser.parse_args()

    start(
        keep_screen_awake=args.keep_screen_awake,
    )


if __name__ == "__main__":
    main()
