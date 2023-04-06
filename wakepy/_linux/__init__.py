"""This module provides the set_keepawake and unset_keepawake
functions for linux. It tries, in this order

(1) jeepney (pure python solution)
(2) dbus-python (python bindings to dbus/libdbus)
(3) systemd (requires sudo!)

Other possibilities: (not implemented)
(4) dbus-send: https://dbus.freedesktop.org/doc/dbus-send.1.html 
"""
from ..exceptions import NotSupportedError

try:
    # jeepney (pure python solution) + D-Bus
    # Requires session message bus (dbus-daemon) running
    from ._jeepney_dbus import set_keepawake, unset_keepawake, METHOD
except NotSupportedError:
    pass

try:
    # dbus-python (python bindings to dbus/libdbus)
    # Requires libdbus + session message bus (dbus-daemon) running
    from ._dbus import set_keepawake, unset_keepawake, METHOD
except NotSupportedError:
    pass

try:
    # Requires sudo and systemd (but no D-Bus)
    from ._systemd import set_keepawake, unset_keepawake, METHOD
except NotSupportedError:
    pass

if "METHOD" not in locals():
    raise NotImplementedError(
        "wakepy does only support dbus and systemd based solutions "
        "Pull requests welcome: https://github.com/np-8/wakepy"
    )

print(f"Wakepy using: {METHOD}")
