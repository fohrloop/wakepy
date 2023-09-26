"""This module provides the set_keepawake and unset_keepawake
functions for linux. It tries, in this order

(1) jeepney (pure python solution)
(2) dbus-python (python bindings to dbus/libdbus)
(3) systemd (requires sudo!)

Other possibilities: (not implemented)
(4) dbus-send: https://dbus.freedesktop.org/doc/dbus-send.1.html 
"""
import os
from importlib import import_module

# Some environment variables
WAKEPY_FAKE_SUCCESS = "WAKEPY_FAKE_SUCCESS"


def should_fake_success() -> bool:
    """Function which says if fake success should be enabled

    Fake success is controlled via WAKEPY_FAKE_SUCCESS environment variable.
    If that variable is set to non-empty value, fake success is activated.

    Motivation:
    -----------
    When running on CI system, wakepy might fail to acquire an inhibitor lock
    just because there is no Desktop Environment running. In these cases, it
    might be useful to just tell with an environment variable that wakepy
    should fake the successful inhibition anyway. Faking the success is done
    after every other method is tried (and failed).
    """
    return bool(os.environ.get(WAKEPY_FAKE_SUCCESS))


for module in "_jeepney_dbus", "_dbus", "_systemd":
    try:
        my_module = import_module(f".{module}", "wakepy._deprecated._linux")
        set_keepawake, unset_keepawake = (
            my_module.set_keepawake,
            my_module.unset_keepawake,
        )
        break
    except NotImplementedError:
        pass
else:
    if should_fake_success():
        # User asked to fake success anyway (Probably running in CI env)
        def set_keepawake(keep_screen_awake=False):
            return False

        def unset_keepawake():
            return False

    else:
        raise NotImplementedError(
            "You've tried to use the deprecated method to set a wakelock and all the"
            " methods have failed.",
        )
