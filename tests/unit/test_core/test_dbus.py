from wakepy.core.dbus import DbusMethod, DbusMethodCall, DbusAddress, BusType
import pytest


session_manager = DbusAddress(
    bus=BusType.SESSION,
    service="org.gnome.SessionManager",
    path="/org/gnome/SessionManager",
    interface="org.gnome.SessionManager",
)


@pytest.fixture
def method_inhibit():
    return DbusMethod(
        name="Inhibit",
        signature="susu",
        params=("app_id", "toplevel_xid", "reason", "flags"),
        output_signature="u",
        output_params=("inhibit_cookie",),
    )


@pytest.fixture
def args_for_inhibit():
    return "first", 123, "third", 567


def test_dbus_method_to_call(method_inhibit, args_for_inhibit):
    method_inhibit = method_inhibit.of(session_manager)

    call = method_inhibit.to_call(args_for_inhibit)

    assert isinstance(call, DbusMethodCall)
    assert call.args == args_for_inhibit
    assert call.method == method_inhibit


def test_dbus_method_to_call_not_fully_defined_method(method_inhibit, args_for_inhibit):
    # The method is not fully defined as it is not tied to any address.
    with pytest.raises(
        ValueError, match="DbusMethodCall requires completely defined DBusMethod"
    ):
        method_inhibit.to_call(args_for_inhibit)
