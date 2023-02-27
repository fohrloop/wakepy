from wakepy.exceptions import NotSupportedError

try:
    import dbus, os, psutil
except ImportError as e:
    print(
        f"Error when importing DBus, os and psutil module: {e}\n\
Root permissions will be needed to set/unset the wakelock!"
    )
    raise NotSupportedError()


# Variable that stores the DBus inhibit for later controlled release.
dbus_inhibit = None

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
        psutil.Process(os.getpid()).name(),
        f"wakepy.set_keepawake(keep_screen_awake={keep_screen_awake})",
    )


def unset_keepawake():
    pm_interface.UnInhibit(dbus_inhibit)
