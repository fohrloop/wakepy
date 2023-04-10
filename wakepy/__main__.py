if __name__ == "__main__":
    """Start wakepy keepawake with CLI

    This is called either with

        python -m wakepy [args]

    or using the executable

        wakepy [args]
    """
    import argparse

    from wakepy._cli import start
    from wakepy.constants import (
        MethodNameLinux,
        MethodNameMac,
        MethodNameWindows,
        OnFailureStrategyName,
    )

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

    parser.add_argument(
        "--on-failure",
        help=(
            "Tells what to do when setting or unsetting fails. This is done when "
            "*every* (selected) method has failed. Default: 'error'."
        ),
        default="error",
        choices=[x.value for x in OnFailureStrategyName.__members__.values()],
    )

    parser.add_argument(
        "--on-method-failure",
        help=(
            "Tells what to do when a method fails. Makes sense only when there are "
            "multiple methods used (like on linux; see `--method-linux`). "
            "See also: `--on-failure`. Default: 'loginfo'."
        ),
        default="loginfo",
        choices=[x.value for x in OnFailureStrategyName.__members__.values()],
    )

    parser.add_argument(
        "--method-linux",
        help=("The method to use on linux."),
        default=None,
        nargs="*",
        choices=[x.value for x in MethodNameLinux.__members__.values()],
    )
    parser.add_argument(
        "--method-win",
        help=("The method to use on windows."),
        default=None,
        nargs="*",
        choices=[x.value for x in MethodNameWindows.__members__.values()],
    )
    parser.add_argument(
        "--method-mac",
        help=("The method to use on MacOS."),
        default=None,
        nargs="*",
        choices=[x.value for x in MethodNameMac.__members__.values()],
    )

    args = parser.parse_args()

    start(
        keep_screen_awake=args.keep_screen_awake,
        on_failure=args.on_failure,
        on_method_failure=args.on_method_failure,
        method_linux=args.method_linux,
        method_win=args.method_win,
        method_mac=args.method_mac,
    )
