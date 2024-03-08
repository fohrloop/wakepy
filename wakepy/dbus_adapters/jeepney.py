from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection
from jeepney.wrappers import unwrap_msg

from wakepy.core import DbusAdapter, DbusMethodCall


class DbusNotFoundError(RuntimeError):
    ...


class JeepneyDbusAdapter(DbusAdapter):
    """An implementation of :class:`~wakepy.DbusAdapter` using `jeepney <https://jeepney.readthedocs.io/>`_.
    Can be used to process DbusMethodCalls (communication with Dbus services
    over a dbus-daemon).
    """

    # timeout for dbus calls, in seconds
    timeout = 2

    def process(self, call: DbusMethodCall):
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
        try:
            connection = open_dbus_connection(bus=call.method.bus)
        except KeyError as exc:
            if "DBUS_SESSION_BUS_ADDRESS" in str(exc):
                raise DbusNotFoundError(
                    "The environment variable DBUS_SESSION_BUS_ADDRESS is not set! "
                    "To use dbus-based methods with jeepney, a session (not system) "
                    "bus (dbus-daemon process) must be running, and the address of the "
                    "bus should be available at the DBUS_SESSION_BUS_ADDRESS "
                    "environment variable. To check if you're running a session "
                    "dbus-daemon, run `ps -x | grep dbus-daemon`"
                ) from exc
        reply = connection.send_and_get_reply(msg, timeout=self.timeout)
        resp = unwrap_msg(reply)
        return resp
