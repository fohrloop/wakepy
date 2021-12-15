import platform


def option_to_string(option):
    if option == True:
        return "x"
    elif option == False:
        return " "
    return "?"


WAKEPY_TEXT_TEMPLATE = r"""                  _                       
                 | |                      
 __      __ __ _ | | __ ___  _ __   _   _ 
 \ \ /\ / // _` || |/ // _ \| '_ \ | | | |
  \ V  V /| (_| ||   <|  __/| |_) || |_| |
   \_/\_/  \__,_||_|\_\\___|| .__/  \__, |
{VERSION_STRING}        | |      __/ |
                            |_|     |___/ """


def wakepy_text():
    from wakepy import __version__

    return WAKEPY_TEXT_TEMPLATE.format(VERSION_STRING=f"{'  v.'+__version__: <20}")


def print_on_start(keep_screen_awake):
    """
    Parameters
    ----------
    keep_screen_awake: bool
        The option to select if screen is to
        be kept on.
    """
    # E.g.: 'windows', 'linux', or 'darwin'
    system = platform.system().lower()
    not_logging_out_automatically = None
    if system == "windows":
        not_logging_out_automatically = keep_screen_awake
    print(wakepy_text())
    list_to_print = (
        (
            True,
            "Your computer will not sleep automatically",
        ),
        (keep_screen_awake, "Screen is kept on"),
        (
            not_logging_out_automatically,
            "You will not be logged out automatically",
        ),
    )
    question_marks_printed = False
    for setting_value, text in list_to_print:
        setting_value_as_string = option_to_string(setting_value)
        print(f" [{setting_value_as_string}] {text}")
        if setting_value_as_string == "?":
            question_marks_printed = True
    print(" (unless battery goes under critical level)")
    if question_marks_printed:
        print(
            """\nThe reason you are seeing "[?]" is because the feature is untested on your platform."""
            """\nIf you wish, you can contribute and inform the behaviour at https://github.com/np-8/wakepy"""
        )
    print(" ")
