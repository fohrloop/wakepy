# mypy: disable-error-code="no-any-unimported"

from __future__ import annotations

import typing
from typing import cast

from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import DBusConnection, open_dbus_connection
from jeepney.wrappers import unwrap_msg

from wakepy.core import DBusAdapter, DBusMethodCall
from wakepy.core.dbus import BusType

if typing.TYPE_CHECKING:
    from typing import Optional, Union

    TypeOfBus = Optional[Union[BusType, str]]


class DBusNotFoundError(RuntimeError): ...


class JeepneyDBusAdapter(DBusAdapter):
    """An implementation of :class:`~wakepy.DBusAdapter` using `jeepney <https://jeepney.readthedocs.io/>`_.
    Can be used to process DBusMethodCalls (communication with DBus services
    over a dbus-daemon).
    """

    # timeout for dbus calls, in seconds
    timeout = 2

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

        connection = cast(DBusConnection, self._get_connection(call.method.bus))
        reply = connection.send_and_get_reply(msg, timeout=self.timeout)
        resp = unwrap_msg(reply)
        return resp

    def _create_new_connection(
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

    def close_connection(self, connection: DBusConnection) -> None:
        connection.close()
