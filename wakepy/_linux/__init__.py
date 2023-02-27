"""This module provides the set_keepawake and unset_keepawake
functions for linux. It tries, in this order

(1) jeepney (pure python solution)
(2) dbus-python (python bindings to dbus/libdbus)
(3) systemd (requires sudo!)

Other possibilities: (not implemented)
(4) dbus-send: https://dbus.freedesktop.org/doc/dbus-send.1.html 
"""
from importlib import import_module
from wakepy.exceptions import NotSupportedError


for module in "_jeepney_dbus", "_dbus", "_systemd":
    try:
        my_module = import_module(f".{module}", f"wakepy._linux")
        set_keepawake, unset_keepawake = (
            my_module.set_keepawake,
            my_module.unset_keepawake,
        )
        break
    except NotSupportedError:
        pass
else:
    raise NotImplementedError(
        "wakepy does only support dbus and systemd based solutions "
        "Pull requests welcome: https://github.com/np-8/wakepy"
    )

print(f"Wakepy using: {my_module.METHOD}")
