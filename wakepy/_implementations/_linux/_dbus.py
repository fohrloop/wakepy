"""This module provides pure python dbus inhibit based set_keepawake
and unset_keepawake for linux

Requires jeepney. Install with:
    python -m pip install jeepney 

See also:
    https://people.freedesktop.org/~hadess/idle-inhibition-spec/re01.html


The inhibitors can be checked with
    dbus-send --print-reply --dest=org.gnome.SessionManager /org/gnome/SessionManager org.gnome.SessionManager.GetInhibitors

For example:

$ dbus-send --print-reply --dest=org.gnome.SessionManager /org/gnome/SessionManager org.gnome.SessionManager.GetInhibitors
method return time=1681201482.075825 sender=:1.25 -> destination=:1.559 serial=465 reply_serial=2
   array [
      object path "/org/gnome/SessionManager/Inhibitor7"
   ]

This can be examined further with

dbus-send --print-reply --dest=org.gnome.SessionManager /org/gnome/SessionManager/InhibitorN org.gnome.SessionManager.Inhibitor.GetAppId

For example:

niko@niko-ubuntu-home:~$ dbus-send --print-reply --dest=org.gnome.SessionManager /org/gnome/SessionManager/Inhibitor7 org.gnome.SessionManager.Inhibitor.GetAppId
method return time=1681203094.197509 sender=:1.25 -> destination=:1.684 serial=480 reply_serial=2
   string "wakepy"
"""

from ...exceptions import KeepAwakeError


SCREENSAVER_BUS_NAME = "org.freedesktop.ScreenSaver"
SCREENSAVER_OBJECT_PATH = "/org/freedesktop/ScreenSaver"
SCREENSAVER_INTERFACE = SCREENSAVER_BUS_NAME

# Values for wakepy.core (for error handling / logging)
PRINT_NAME = "jeepney (dbus)"
REQUIREMENTS = [
    "session message bus (dbus-daemon) running",
    "DBUS_SESSION_BUS_ADDRESS set",
    "jeepney (python package)",
]

module_initialized = False
# The cookie holds represents the inhibition request
# It is given in the response of the inhibit call and
# used in the uninhibit call
cookie = None
# This can create dbus messages. Created only if needed.
messagegenerator = None
# This is the connection to the session message bus. Created only if needed.
connection = None


def init_module():
    """initializes this module. The 3rd party imports must be made when we need
    them, not when we import this module. as we want any exceptions occur only
    when the keepawake functions like `set_keepawake` are used, not when
    they're imported.

    We also need to subclass the imported MessageGenerator, create instance
    of it and create a connection to the session messsage bus.
    """

    global connection, messagegenerator, module_initialized

    try:
        from jeepney.wrappers import MessageGenerator, new_method_call
        from jeepney.io.blocking import open_dbus_connection
    except ImportError as e:
        raise KeepAwakeError("Could not import jeepney!") from e

    class ScreenSaveMessageGenerator(MessageGenerator):
        r"""DBus interface to org.freedesktop.Screensaver"""
        interface = SCREENSAVER_INTERFACE

        def __init__(
            self,
            object_path=SCREENSAVER_OBJECT_PATH,
            bus_name=SCREENSAVER_BUS_NAME,
        ):
            super().__init__(object_path=object_path, bus_name=bus_name)

        def inhibit(self, application_name, reason_for_inhibit):
            return new_method_call(
                self, "Inhibit", "ss", (application_name, reason_for_inhibit)
            )

        def uninhibit(self, cookie):
            return new_method_call(self, "UnInhibit", "u", (cookie,))

    messagegenerator = ScreenSaveMessageGenerator()

    try:
        connection = open_dbus_connection(bus="SESSION")
    except KeyError as e:
        if "DBUS_SESSION_BUS_ADDRESS" in str(e):
            raise KeepAwakeError(
                "DBUS_SESSION_BUS_ADDRESS environment variable not set! "
                "If running in subprocess, make sure to pass the DBUS_SESSION_BUS_ADDRESS "
                "environment variable."
            ) from e
        raise KeepAwakeError(
            "Could not set dbus connection to session message bus. "
        ) from e

    module_initialized = True


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
    if not module_initialized:
        init_module()

    global cookie
    msg_inhibit = messagegenerator.inhibit("wakepy", "wakelock active")
    reply = connection.send_and_get_reply(msg_inhibit)
    cookie = reply.body[0]


def unset_keepawake():
    if cookie is None:
        raise KeepAwakeError("You must set_keepawake before unsetting!")
    msg_uninhibit = messagegenerator.uninhibit(cookie)
    connection.send_and_get_reply(msg_uninhibit)


def check_keepawake():
    if not module_initialized:
        init_module()
