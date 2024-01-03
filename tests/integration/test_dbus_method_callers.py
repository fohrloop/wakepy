from jeepney import DBusAddress, MessageType, new_method_call
from jeepney.io.blocking import open_dbus_connection


# TODO: Replace this with tests for DbusAdapter. The only reason to use
# a fake Dbus service on a private session bus is to test DbusAdapters.
def test_session_manager(private_bus):
    addr = DBusAddress(
        object_path="/org/github/wakepy/TestManager",
        bus_name="org.github.wakepy.TestManager",
        # interface="org.github.wakepy.TestManager.Numbers",
    )
    with open_dbus_connection(private_bus) as connection:
        first_number, second_number = 5, 6

        for first_number, second_number in ((5, 6), (7, 8), (10, 11)):
            msg = new_method_call(
                addr, "TestSimpleNumberAdd", "uu", (first_number, second_number)
            )
            reply = connection.send_and_get_reply(msg, timeout=2)

            if reply.header.message_type == MessageType.error:
                raise RuntimeError()
            assert reply.body[0] == first_number + second_number
