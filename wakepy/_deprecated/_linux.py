"""This module provides pure python dbus inhibit based set_keepawake
and unset_keepawake for linux

Requires jeepney. Install with:
    python -m pip install jeepney 

See also:
    https://people.freedesktop.org/~hadess/idle-inhibition-spec/re01.html

"""


class KeepAwakeError(Exception):
    ...

from dataclasses import dataclass

# temporarily here.
# TODO: move to better place.
@dataclass
class InhibitorInfo:
    # The application mame
    app_name: str

    # The reason, if any
    reason: str


class KeepAwakeInfo:
    def __init__(self, inhibitors: list[InhibitorInfo] | None = None):
        self.inhibitors = inhibitors or []

    def add(self, inhibitor: InhibitorInfo):
        self.inhibitors.append(inhibitor)

    @property
    def n_inhibitors(self) -> int:
        return len(self.inhibitors)

    @property
    def keepawake(self) -> bool:
        return bool(self.inhibitors)



# There will be imported from jeepney when needed
new_method_call = None
DBusAddress = None
open_dbus_connection = None

# Values for wakepy.core (for error handling / logging)
PRINT_NAME = "jeepney (dbus)"
REQUIREMENTS = [
    "session message bus (dbus-daemon) running",
    "DBUS_SESSION_BUS_ADDRESS set",
    "jeepney (python package)",
]

# The keepawake setter / unsetter object
# Will be None until first call of methods
setter = None


def import_jeepney():
    global new_method_call, DBusAddress, open_dbus_connection

    try:
        from jeepney import new_method_call, DBusAddress
        from jeepney.io.blocking import open_dbus_connection
    except Exception as e:
        raise KeepAwakeError("Could not import jeepney!") from e


def get_connection(bus="SESSION"):
    """Get a DBus connection. Note that any Inhibits are removed if the
    connection is closed."""

    try:
        return open_dbus_connection(bus=bus)
    except Exception as e:
        if "DBUS_SESSION_BUS_ADDRESS" in str(e):
            raise KeepAwakeError(
                "DBUS_SESSION_BUS_ADDRESS environment variable not set! "
                "If running in subprocess, make sure to pass the DBUS_SESSION_BUS_ADDRESS "
                "environment variable."
            ) from e
        raise KeepAwakeError(
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
            raise KeepAwakeError("You must set_keepawake before unsetting!")

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


def _get_inhibitor_and_reason(connection, obj_path: str):
    addr = DBusAddress(
        obj_path,
        bus_name="org.gnome.SessionManager",
        interface="org.gnome.SessionManager.Inhibitor",
    )

    def _get(method):
        msg = new_method_call(addr, method, "", tuple())
        reply = connection.send_and_get_reply(msg)
        return reply.body[0]

    name = _get("GetAppId")
    reason = _get("GetReason")

    return name, reason


def check_keepawake() -> KeepAwakeInfo:
    """Checks keepawake status (dbus). Experimental."""
    try:
        return check_keepawake_gnome()
    except Exception as e:
        raise KeepAwakeError(f"Cannot check keepawake! Reason: {str(e)}") from e


def check_keepawake_gnome() -> KeepAwakeInfo:
    """Checks keepawake status on gnome (dbus). Experimental."""
    info = KeepAwakeInfo()

    if DBusAddress is None:
        import_jeepney()

    gnome_session_manager_addr = DBusAddress(
        "/org/gnome/SessionManager",  # DBus object path
        bus_name="org.gnome.SessionManager",
        interface="org.gnome.SessionManager",
    )
    msg = new_method_call(
        gnome_session_manager_addr,  # DBusAddress
        "GetInhibitors",  # Method
        "",  # No input for method
        tuple(),
    )
    connection = get_connection()
    reply = connection.send_and_get_reply(msg)

    for inhibitor_tuple in reply.body[0]:
        inhibitor_name, inhibitor_reason = _get_inhibitor_and_reason(
            connection, inhibitor_tuple
        )
        info.add(InhibitorInfo(inhibitor_name, inhibitor_reason))

    return info
