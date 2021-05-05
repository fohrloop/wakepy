import argparse

parser = argparse.ArgumentParser(
    prog="wakepy",
    formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=27),
)

parser.add_argument(
    "-s",
    "--keep-screen-awake",
    help="Keep also the screen awake. On Linux, this flag is set on and cannot be disabled.",
    action="store_true",
    default=False,
)
if __name__ == "__main__":
    from wakepy import start

    args = parser.parse_args()

    start(keep_screen_awake=args.keep_screen_awake)
