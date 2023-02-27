"""This module provides the systemd based solution for linux 

See:
https://www.man7.org/linux/man-pages/man1/systemctl.1.html
"""
import subprocess
import os
import sys

from wakepy.exceptions import NotSupportedError

METHOD = "systemd"
print("wakepy: falling back using systemd. ")

try:
    subprocess.check_output(["pidof", "systemd"])
except subprocess.CalledProcessError:
    # if 'pidof' does not find a process it will return with non-zero exit
    # status, check_output will raise subprocess.CalledProcessError
    # See: https://github.com/np-8/wakepy/pull/3
    raise NotSupportedError("sysmtemd not supported")

if not "SUDO_UID" in os.environ.keys():
    print(
        "ERROR! Root permissions will be needed to set/unset the wakelock with systemd!"
        """\n\nExample: sudo -E "PATH=$PATH" python -m wakepy"""
    )
    sys.exit()


def run_systemctl(command):
    args = ["sleep.target", "suspend.target", "hibernate.target", "hybrid-sleep.target"]
    subprocess.run(["systemctl", command, *args])


def set_keepawake(keep_screen_awake=False):
    """
    Set the keep-awake. During keep-awake, the CPU is not allowed to go to
    sleep automatically until the `unset_keepawake` is called.

    Parameters
    -----------
    keep_screen_awake: bool
        Currently unused as the screen will remain active as a byproduct of
        preventing sleep.
    """
    run_systemctl("mask")


def unset_keepawake():
    run_systemctl("unmask")
