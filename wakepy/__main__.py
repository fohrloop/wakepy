import argparse

parser = argparse.ArgumentParser(prog="wakepy")

parser.add_argument(
    "-s",
    "--keep-screen-awake",
    help="Keep also the screen awake.",
    action="store_true",
    default=False,
)
if __name__ == "__main__":
    from wakepy import start

    args = parser.parse_args()

    start(keep_screen_awake=args.keep_screen_awake)
