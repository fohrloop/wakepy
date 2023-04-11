"""This module contains system related functions and constants

Important module-level variables
---------------------------------
# E.g. 'windows', 'darwin', 'linux'
CURRENT_SYSTEM

# E.g. 'windows', 'darwin', 'gnome', 'unknown'
CURRENT_DESKTOP_ENVIRONMENT
"""

import os
import re
import platform
import subprocess

from constants import SystemName

# Usually a SystemName
# E.g.: 'windows', 'linux' or 'darwin'
CURRENT_SYSTEM = platform.system().lower()

DESKTOP_SESSIONS = [
    "gnome",
    "unity",
    "cinnamon",
    "mate",
    "xfce4",
    "lxde",
    "fluxbox",
    "blackbox",
    "openbox",
    "icewm",
    "jwm",
    "afterstep",
    "trinity",
    "kde",
]


def get_desktop_environment() -> str:
    """A lowercase name of current desktop environment.

    Not 100% accurate as it just depends on bunch of
    environment variables, but can provide good first guess.

    This will not work in isolated process, like with tox if
    the environment variables are not passed to them.

    Returns
    -------
    environment
        The desktop environment. If not known, returns "unknown"
    """
    if CURRENT_SYSTEM in {SystemName.WINDOWS, SystemName.DARWIN}:
        return CURRENT_SYSTEM
    return get_unix_desktop_environment()


def get_unix_desktop_environment() -> str:
    """A lowercase name of current desktop environment.

    Adopted with edits from https://stackoverflow.com/a/21213358/3015186

    Not 100% accurate as it just depends on bunch of
    environment variables, but can provide good first guess.

    This will not work in isolated process, like with tox if
    the environment variables are not passed to them.

    Returns
    -------
    environment
        The desktop environment. If not known, returns "unknown"
    """

    desktop_session = os.environ.get("DESKTOP_SESSION")
    if desktop_session is not None:
        desktop_session = desktop_session.lower()
        if desktop_session in DESKTOP_SESSIONS:
            return desktop_session
        ## Special cases ##
        # Canonical sets $DESKTOP_SESSION to Lubuntu rather than LXDE if using LXDE.
        # There is no guarantee that they will not do the same with the other desktop environments.
        elif "xfce" in desktop_session or desktop_session.startswith("xubuntu"):
            return "xfce4"
        elif desktop_session.startswith("ubuntustudio"):
            return "kde"
        elif desktop_session.startswith("ubuntu"):
            return "gnome"
        elif desktop_session.startswith("lubuntu"):
            return "lxde"
        elif desktop_session.startswith("kubuntu"):
            return "kde"
        elif desktop_session.startswith("razor"):  # e.g. razorkwin
            return "razor-qt"
        elif desktop_session.startswith("wmaker"):  # e.g. wmaker-common
            return "windowmaker"
    if os.environ.get("KDE_FULL_SESSION") == "true":
        return "kde"
    elif os.environ.get("GNOME_DESKTOP_SESSION_ID"):
        if not "deprecated" in os.environ.get("GNOME_DESKTOP_SESSION_ID"):
            return "gnome2"
    # From http://ubuntuforums.org/showthread.php?t=652320
    elif is_running_unix("xfce-mcs-manage"):
        return "xfce4"
    elif is_running_unix("ksmserver"):
        return "kde"
    return "unknown"


def is_running_unix(process):
    s = subprocess.Popen(["ps", "axw"], stdout=subprocess.PIPE)
    for x in s.stdout:
        if re.search(process, x.decode("utf-8")):
            return True
    return False


CURRENT_DESKTOP_ENVIRONMENT = get_desktop_environment()
