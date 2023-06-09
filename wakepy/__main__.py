"""Start wakepy keepawake with CLI

This is called either with

    python -m wakepy [args]

or using the executable

    wakepy [args]
"""
import argparse

from wakepy._cli import start


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
            "Keep programs running; inhibit automatic sleep/suspend. This is"
            " used as a default if no modes are selected."
        ),
    )

    add_mode(
        "-p",
        "--presentation",
        help=("Presentation mode; inhibit automatic sleep, screensaver and screenlock"),
    )
    add_mode(
        "-s",
        "--keep-screen-awake",
        help=(
            "[DEPRECATED] Keep also the screen awake. "
            "On Linux, this flag is set on and cannot be disabled."
        ),
    )
    return parser


def parse_arguments(parser: argparse.ArgumentParser) -> dict[str, bool]:
    args = parser.parse_args()

    if args.keep_screen_awake and any((args.keep_running, args.presentation)):
        raise ValueError(
            "The deprecated --keep-screen-awake option cannot be used with the new"
            " options!"
        )

    if args.keep_screen_awake:
        # Deprecated in 0.7.0 -> remove in later release.
        deprecation_warning = True
        args.presentation = args.keep_screen_awake
    else:
        deprecation_warning = False

    if not any((args.keep_running, args.presentation, args.keep_screen_awake)):
        # The default action, if nothing is selected, is "keep running"
        args.keep_running = True

    return dict(
        keep_running=args.keep_running,
        presentation_mode=args.presentation,
        deprecation_warning=deprecation_warning,
    )


def main():
    parser = get_argparser()
    kwargs = parse_arguments(parser)
    start(**kwargs)


if __name__ == "__main__":
    main()
