"""This module provides pure python dbus inhibit based set_keepawake
and unset_keepawake for linux

Requires jeepney. Install with:
    python -m pip install jeepney 

See also:
    https://people.freedesktop.org/~hadess/idle-inhibition-spec/re01.html

"""

# There will be imported from jeepney when needed
new_method_call = None
DBusAddress = None
open_dbus_connection = None


# The keepawake setter / unsetter object
# Will be None until first call of methods
setter = None


def import_jeepney():
    global new_method_call, DBusAddress, open_dbus_connection

    try:
        from jeepney import DBusAddress, new_method_call
        from jeepney.io.blocking import open_dbus_connection
    except Exception as e:
        raise NotImplementedError("Could not import jeepney!") from e


def get_connection(bus="SESSION"):
    """Get a DBus connection. Note that any Inhibits are removed if the
    connection is closed."""

    try:
        return open_dbus_connection(bus=bus)
    except Exception as e:
        if "DBUS_SESSION_BUS_ADDRESS" in str(e):
            raise NotImplementedError(
                "DBUS_SESSION_BUS_ADDRESS environment variable not set! "
                "If running in subprocess, make sure to pass the "
                "DBUS_SESSION_BUS_ADDRESS environment variable."
            ) from e
        raise NotImplementedError(
            f"Could not set dbus connection to {bus} message bus.\n"
            f"{e.__class__.__name__}: {str(e)}"
        ) from e


class KeepAwakeSetter:
    def __init__(self):
        if DBusAddress is None:
            import_jeepney()

        self.screensaver = DBusAddress(
            "/org/freedesktop/ScreenSaver",  # DBus object path
            bus_name="org.freedesktop.ScreenSaver",
            interface="org.freedesktop.ScreenSaver",
        )

        # The cookie holds represents the inhibition request
        # It is given in the response of the inhibit call and
        # used in the uninhibit call
        self.cookie = None
        self.connection = get_connection("SESSION")

    def set_keepawake(self, keep_screen_awake=False):
        """
        Set the keep-awake. During keep-awake, the CPU is not allowed to go to
        sleep automatically until the `unset_keepawake` is called.

        Parameters
        -----------
        keep_screen_awake: bool
            Currently unused as the screen will remain active as a byproduct of
            preventing sleep.
        """

        msg_inhibit = new_method_call(
            self.screensaver,  # DBusAddress
            "Inhibit",  # Method
            "ss",  # Means: two strings as input for method
            ("wakepy", "wakelock active"),
        )

        reply = self.connection.send_and_get_reply(msg_inhibit)
        self.inhibit_cookie = reply.body[0]

    def unset_keepawake(self):
        if self.inhibit_cookie is None:
            raise NotImplementedError("You must set_keepawake before unsetting!")

        msg_uninhibit = new_method_call(
            self.screensaver,
            "UnInhibit",  # Method
            "u",  # Means: UInt32 input for method
            (self.inhibit_cookie,),
        )

        self.connection.send_and_get_reply(msg_uninhibit)
        self.inhibit_cookie = None


def get_setter():
    global setter
    if setter is None:
        setter = KeepAwakeSetter()
    return setter


def set_keepawake(keep_screen_awake=False):
    setter = get_setter()
    setter.set_keepawake(keep_screen_awake=keep_screen_awake)


def unset_keepawake():
    setter = get_setter()
    setter.unset_keepawake()
