import subprocess

COMMAND = u"systemctl"
ARGS = [u"sleep.target", u"suspend.target", u"hibernate.target", u"hybrid-sleep.target"]
# https://www.man7.org/linux/man-pages/man1/systemctl.1.html

try:
    subprocess.check_output(["pidof", "systemd"])
except subprocess.CalledProcessError:
    # if 'pidof' does not find a process it will return with non-zero exit status, check_output will raise subprocess.CalledProcessError
    # See: https://github.com/np-8/wakepy/pull/3
    raise NotImplementedError(
        "wakepy has not yet support for init processes other than systemd. Pull requests welcome: https://github.com/np-8/wakepy"
    )


def set_keepawake(keep_screen_awake=False):
    """
    Set the keep-awake. During keep-awake, the CPU is not allowed to go to sleep
    automatically until the `unset_keepawake` is called.

    Parameters
    -----------
    keep_screen_awake: bool
        Currently unused as the screen will remain active as a byproduct of preventing sleep.
    """
    subprocess.run([COMMAND, u"mask", *ARGS])


def unset_keepawake():
    subprocess.run([COMMAND, u"unmask", *ARGS])
