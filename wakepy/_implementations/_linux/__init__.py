"""This module provides the set_keepawake and unset_keepawake
functions for linux. It tries, in this order

(1) jeepney (pure python solution)
(2) dbus-python (python bindings to dbus/libdbus)
(3) systemd (requires sudo!)

Other possibilities: (not implemented)
(4) dbus-send: https://dbus.freedesktop.org/doc/dbus-send.1.html 
"""


# from ._dbus import method as jeepney_method


# try:
#     # dbus-python (python bindings to dbus/libdbus)
#     # Requires libdbus + session message bus (dbus-daemon) running
#     from ._dbus import set_keepawake, unset_keepawake, METHOD
# except NotSupportedError:
#     pass

# try:
#     # Requires sudo and systemd (but no D-Bus)
#     from ._systemd import set_keepawake, unset_keepawake, METHOD
# except NotSupportedError:
#     pass

# methods = {method.shortname: method for method in (jeepney_method,)}
