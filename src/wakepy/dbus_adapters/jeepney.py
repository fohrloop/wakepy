from __future__ import annotations

import typing

from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection
from jeepney.wrappers import unwrap_msg

from wakepy.core import DBusAdapter, DBusMethodCall
from wakepy.core.dbus import BusType

if typing.TYPE_CHECKING:
    from typing import Dict, Optional, Union

    from jeepney.io.blocking import DBusConnection

    TypeOfBus = Optional[Union[BusType, str]]


class DBusNotFoundError(RuntimeError): ...


class JeepneyDBusAdapter(DBusAdapter):
    """An implementation of :class:`~wakepy.DBusAdapter` using `jeepney <https://jeepney.readthedocs.io/>`_.
    Can be used to process DBusMethodCalls (communication with DBus services
    over a dbus-daemon).
    """

    # timeout for dbus calls, in seconds
    timeout = 2

    def __init__(self) -> None:
        self._connections: Dict[TypeOfBus, DBusConnection] = dict()  # type: ignore[no-any-unimported]

    def process(self, call: DBusMethodCall) -> object:
        addr = DBusAddress(
            object_path=call.method.path,
            bus_name=call.method.service,
            interface=call.method.interface,
        )

        msg = new_method_call(
            addr,
            method=call.method.name,
            signature=call.method.signature,
            body=call.args,
        )

        connection = self._get_connection(call.method.bus)
        reply = connection.send_and_get_reply(msg, timeout=self.timeout)
        resp = unwrap_msg(reply)
        return resp

    def _get_connection(  # type: ignore[no-any-unimported]
        self, bus: TypeOfBus = BusType.SESSION
    ) -> DBusConnection:
        """Gets either a new connection or a cached one, if there is such.
        Caching of connections is done on bus level."""

        if bus in self._connections:
            return self._connections[bus]

        connection = self._create_new_connection(bus)

        self._connections[bus] = connection
        return connection

    def _create_new_connection(  # type: ignore[no-any-unimported]
        self, bus: TypeOfBus = BusType.SESSION
    ) -> DBusConnection:
        try:
            return open_dbus_connection(bus=bus)
        except KeyError as exc:
            if "DBUS_SESSION_BUS_ADDRESS" in str(exc):
                raise DBusNotFoundError(
                    "The environment variable DBUS_SESSION_BUS_ADDRESS is not set! "
                    "To use dbus-based methods with jeepney, a session (not system) "
                    "bus (dbus-daemon process) must be running, and the address of the "
                    "bus should be available at the DBUS_SESSION_BUS_ADDRESS "
                    "environment variable. To check if you're running a session "
                    "dbus-daemon, run `ps -x | grep dbus-daemon`"
                ) from exc
            else:
                raise
