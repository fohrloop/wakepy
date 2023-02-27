"""This module provides pure python dbus inhibit based set_keepawake
and unset_keepawake for linux

Requires jeepney. Install with:
    python -m pip install jeepney 

See also:
    https://people.freedesktop.org/~hadess/idle-inhibition-spec/re01.html
"""
METHOD = "jeepney (dbus)"

from wakepy.exceptions import NotSupportedError

try:
    from jeepney.wrappers import MessageGenerator, new_method_call
    from jeepney.io.blocking import open_dbus_connection
except ImportError as e:
    print(f"Error when importing jeepney: {e}")
    raise NotSupportedError()


SCREENSAVER_BUS_NAME = "org.freedesktop.ScreenSaver"
SCREENSAVER_OBJECT_PATH = "/org/freedesktop/ScreenSaver"
SCREENSAVED_INTERFACE = SCREENSAVER_BUS_NAME

connection = open_dbus_connection(bus="SESSION")

# The cookie holds represents the inhibition request
# It is given in the response of the inhibit call and
# used in the uninhibit call
cookie = None


class ScreenSaveMessageGenerator(MessageGenerator):
    r"""DBus interface to org.freedesktop.Screensaver"""
    interface = SCREENSAVED_INTERFACE

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
    global cookie
    msg_inhibit = messagegenerator.inhibit("wakepy", "wakelock active")
    reply = connection.send_and_get_reply(msg_inhibit)
    cookie = reply.body[0]


def unset_keepawake():
    if cookie is None:
        print("You must set keepawake before unsetting!")
        return
    msg_uninhibit = messagegenerator.uninhibit(cookie)
    connection.send_and_get_reply(msg_uninhibit)
