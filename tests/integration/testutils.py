from __future__ import annotations

import logging
import time
import typing
from typing import Optional, Tuple

from jeepney import HeaderFields, MessageType, new_error, new_method_return
from jeepney.bus_messages import message_bus
from jeepney.io.blocking import open_dbus_connection

if typing.TYPE_CHECKING:
    import queue

    from wakepy.core import DbusAddress

DBUS_REQUEST_NAME_REPLY_PRIMARY_OWNER = 1


class DbusService:
    """A class for defining Dbus services, which can be made available in a
    bus. To define a dbus service, create a subclass and provide

    (1) addr: DbusAddress
        Where the dbus service is located at.
    (2) handle_method
        A function which handles dbus method calls. Use if statements for
        defining what to do if the service provides multiple methods.

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

    addr: DbusAddress

    def __init__(self, bus_address: str, queue_: queue.Queue, stop: typing.Callable):
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
        self._queue = queue_
        self._stop = stop

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
            while not self._stop():
                time.sleep(0.01)
                self.run_loop(connection)

    def reserve_bus_name(self, connection, bus_name):
        """Request a name on the connected message bus; become the primary
        owner of a well-known bus name.

        Raises
        ------
        RunTimeError if could not become the primary owner
        """
        reply = connection.send_and_get_reply(message_bus.RequestName(bus_name))
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
        try:
            msg = connection.receive(timeout=0)
        except TimeoutError:
            return

        if msg.header.message_type != MessageType.method_call:
            raise ValueError("Received non-method call message:", msg)

        method = msg.header.fields[HeaderFields.member]

        out = self.handle_method(method, args=msg.body)

        if out is None:
            rep = self._get_error_message(msg)
        elif (
            isinstance(out, tuple)
            and len(out) == 2
            and isinstance(out[0], str)
            and isinstance(out[1], tuple)
        ):
            output_signature, output = out
            rep = new_method_return(msg, output_signature, output)
        else:
            raise ValueError("The output of handle_method must be Tuple[str, Tuple]!")

        try:
            connection.send_message(rep)
        except Exception as e:
            logging.info("Error occured:" + str(e))
            connection.send_message(self._get_error_message(msg, ".Error.OtherError"))

    def _get_error_message(self, msg, method=".Error.NoMethod"):
        """Create an error message for replying to a message"""
        return new_error(msg, self.bus_name + method)

    def handle_method(self, method: str, args: Tuple) -> Optional[Tuple[str, Tuple]]:
        """Should return either None (when method does not exist), or tuple of
        output signature (like "ii" or "sus", etc.), and output values which
        are of the type defined by the output signature
        """
