from jeepney import new_method_call, DBusAddress
from jeepney.io.blocking import open_dbus_connection
from jeepney.wrappers import unwrap_msg


from wakepy.core.calls import DbusMethodCall
from wakepy.core.dbus import DbusAdapter


class JeepneyDbusAdapter(DbusAdapter):
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
        connection = open_dbus_connection(bus=call.method.bus)
        reply = connection.send_and_get_reply(msg, timeout=self.timeout)
        resp = unwrap_msg(reply)
        return resp
