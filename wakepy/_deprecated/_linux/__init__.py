"""This module provides the set_keepawake and unset_keepawake
functions for linux. It tries, in this order

(1) jeepney (pure python solution)
(2) dbus-python (python bindings to dbus/libdbus)
(3) systemd (requires sudo!)

Other possibilities: (not implemented)
(4) dbus-send: https://dbus.freedesktop.org/doc/dbus-send.1.html 
"""
from importlib import import_module

from ...core.fake import fake_success

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
    if fake_success():
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
