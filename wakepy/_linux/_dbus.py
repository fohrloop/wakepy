"""This module provides dbus-python + libdbus (aka. dbus) based set_keepawake
and unset_keepawake for linux

Requires dbus-python[1] and libdbus (freedesktop reference implementation)
Untested installation instructions[2]: 

    sudo apt install libdbus-glib-1-dev libdbus-1-dev
    python -m pip install dbus-python
    
Note: libdbus has known problems with multi-threaded use! [3]

[1]: https://github.com/freedesktop/dbus-python
[2]: For venvs. Many linux distributions come with pre-installed dbus-python
[3]: https://dbus.freedesktop.org/doc/dbus-python/

"""
from wakepy.exceptions import NotSupportedError

try:
    import dbus
except ImportError as e:
    print(f"Error when importing dbus-python: {e}")
    raise NotSupportedError()


# Variable that stores the DBus inhibit for later controlled release.
dbus_inhibit = None
METHOD = "dbus-python (+libdbus)"

try:
    pm_interface = dbus.Interface(
        dbus.SessionBus().get_object(
            "org.freedesktop.ScreenSaver", "/org/freedesktop/ScreenSaver"
        ),
        "org.freedesktop.ScreenSaver",
    )
except Exception as e:
    print(
        f"Wakepy can't use DBus Inhibit on this system because of a {type(e).__name__}:"
        f" {e}\nroot permissions will be needed to set/release the wakelock."
    )


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

    global dbus_inhibit
    dbus_inhibit = pm_interface.Inhibit(
        "wakepy",
        f"wakepy.set_keepawake(keep_screen_awake={keep_screen_awake})",
    )


def unset_keepawake():
    pm_interface.UnInhibit(dbus_inhibit)
