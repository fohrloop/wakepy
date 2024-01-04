import multiprocessing as mp

from typing import Optional
from jeepney import HeaderFields, MessageType, new_error, new_method_return
from jeepney.bus_messages import message_bus
from jeepney.io.blocking import open_dbus_connection

DBUS_REQUEST_NAME_REPLY_PRIMARY_OWNER = 1


def test_simple_method_add(x: int, y: int):
    return x + y


class DbusService:
    """
    Attributes
    ----------
    bus_address
        The address of the message bus
    bus_name: None | str
        If None, there is no service running. If not None, will be the well-
        known bus name this service has reserved. A DbusService can only have
        one well-known bus name at a time. For example:
        "org.gnome.SessionManager"
    """

    def __init__(self, bus_address: str, queue: Optional[mp.Queue] = None):
        """
        Parameters
        ----------
        bus_address: str
            The address of the bus to connect to. This is taken from the output
            the dbus-daemon command, when launching the daemon. For example:
            "unix:abstract=/tmp/dbus-nK9CkQEvAn,guid=1086b64f32c864a01f31"
        """
        self.bus_address = bus_address
        self.bus_name: None | str = None
        self.object_path: None | str = None
        self._unique_name: None | str = None
        self._queue = queue

    def start(self, server_name: str, object_path: str):
        """
        Parameters
        ----------
        server_name: str
            The "well known bus name" to take; the server name. For example
            "org.gnome.SessionManager"

        """
        self.object_path = object_path

        with open_dbus_connection(self.bus_address) as connection:
            self._unique_name = connection.unique_name
            self.reserve_bus_name(connection, bus_name=server_name)
            while True:
                self.run_loop(connection)

    def reserve_bus_name(self, connection, bus_name):
        """Request a name on the connected message bus; become the primary
        owner of a well-known bus name.

        Raises
        ------
        RunTimeError if could not become the primary owner
        """
        reply = connection.send_and_get_reply(message_bus.RequestName(bus_name))
        if self._queue:
            self._queue.put("ready")

        if reply.body[0] == DBUS_REQUEST_NAME_REPLY_PRIMARY_OWNER:
            # The name had no existing owner, and the caller is now
            # the primary owner; or that the name had an owner, and the caller
            # specified DBUS_NAME_FLAG_REPLACE_EXISTING, and the current owner
            # specified DBUS_NAME_FLAG_ALLOW_REPLACEMENT.
            #
            # Ref: https://dbus.freedesktop.org/doc/api/html/group__DBusBus.html#ga8a9024c78c4ea89b6271f19dbc7861b2
            self.bus_name = bus_name

            return

        raise RuntimeError(
            f"Did not get name {bus_name} from dbus-daemon! :(\n\n"
            "The reason is most likely that someone else took that name first. \n"
            f"Used bus: {self.bus_address}"
        )

    def run_loop(self, connection):
        msg = connection.receive()

        if msg.header.message_type != MessageType.method_call:
            raise ValueError("Received non-method call message:", msg)

        method = msg.header.fields[HeaderFields.member]

        # Dispatch to different methods
        if method == "TestSimpleNumberAdd":
            res = test_simple_method_add(msg.body[0], msg.body[1])
            rep = new_method_return(msg, "i", (res,))
        else:
            rep = new_error(msg, self.bus_name + ".Error.NoMethod")

        connection.send_message(rep)
