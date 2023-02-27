import platform

WAKEPY_TEXT_TEMPLATE = r"""                  _                       
                 | |                      
 __      __ __ _ | | __ ___  _ __   _   _ 
 \ \ /\ / // _` || |/ // _ \| '_ \ | | | |
  \ V  V /| (_| ||   <|  __/| |_) || |_| |
   \_/\_/  \__,_||_|\_\\___|| .__/  \__, |
{VERSION_STRING}        | |      __/ |
                            |_|     |___/ """

WAKEPY_TICKBOXES_TEMPLATE = """
 [x] Your computer will not sleep automatically
 [{screen_kept_on}] Screen is kept on
 [{no_automatic_logout}] You will not be logged out automatically
 (unless battery goes under critical level)
""".strip(
    "\n"
)


def wakepy_text():
    from wakepy import __version__

    return WAKEPY_TEXT_TEMPLATE.format(VERSION_STRING=f"{'  v.'+__version__: <20}")


def get_not_logging_out_automatically(keep_screen_awake: bool) -> bool:
    from wakepy import CURRENT_SYSTEM, System

    not_logging_out_automatically = None
    if CURRENT_SYSTEM == System.WINDOWS:
        not_logging_out_automatically = keep_screen_awake
    return not_logging_out_automatically


def create_wakepy_opts_text(keep_screen_awake: bool) -> str:
    opts = dict(
        no_automatic_logout=get_not_logging_out_automatically(keep_screen_awake),
        screen_kept_on=keep_screen_awake,
    )
    option_to_string = {True: "x", False: " "}

    return WAKEPY_TICKBOXES_TEMPLATE.format(
        **{key: option_to_string.get(val, "?") for key, val in opts.items()}
    )


def print_on_start(keep_screen_awake):
    """
    Parameters
    ----------
    keep_screen_awake: bool
        The option to select if screen is to
        be kept on.
    """

    wakepy_opts_text = create_wakepy_opts_text(keep_screen_awake)

    print(wakepy_text())
    print(wakepy_opts_text)
    if "[?]" in wakepy_opts_text:
        print(
            """\nThe reason you are seeing "[?]" is because the feature is untested """
            "on your platform.\nIf you wish, you can contribute and inform the "
            "behaviour at https://github.com/np-8/wakepy"
        )
    print(" ")
