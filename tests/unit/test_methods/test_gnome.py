import pytest

from wakepy.core import BusType, CallProcessor, DbusAddress, DbusMethod
from wakepy.core.dbus import DbusAdapter
from wakepy.methods.gnome import (
    GnomeFlag,
    GnomeSessionManagerNoIdle,
    GnomeSessionManagerNoSuspend,
)

session_manager = DbusAddress(
    bus=BusType.SESSION,
    service="org.gnome.SessionManager",
    path="org/gnome/SessionManager",
    interface="org.gnome.SessionManager",
)

method_inhibit = DbusMethod(
    name="Inhibit",
    signature="susu",
    params=("app_id", "toplevel_xid", "reason", "flags"),
    output_signature="u",
    output_params=("inhibit_cookie",),
).of(session_manager)

method_uninhibit = DbusMethod(
    name="UnInhibit",
    signature="u",
    params=("inhibit_cookie",),
).of(session_manager)

fake_cookie = 75848243423


@pytest.mark.parametrize(
    "method_cls, flag",
    [
        (GnomeSessionManagerNoSuspend, GnomeFlag.INHIBIT_SUSPEND),
        (GnomeSessionManagerNoIdle, GnomeFlag.INHIBIT_IDLE),
    ],
)
def test_gnome_enter_mode(method_cls, flag):
    class TestAdapter(DbusAdapter):
        def process(self, call):
            assert call.method == method_inhibit
            assert call.args == {
                "app_id": "wakepy",
                "toplevel_xid": 42,
                "reason": "wakelock active",
                "flags": flag,
            }
            return fake_cookie

    # Test the method
    method = method_cls(CallProcessor(dbus_adapter=TestAdapter))

    # Checks before tests: Nothing yet set
    assert method.inhibit_cookie is None

    # cannot exit yet as have not entered
    with pytest.raises(RuntimeError, match="Cannot exit before entering"):
        method.exit_mode()

    # This sets a inhibit_cookie to value returned by the DbusAdapter
    method.enter_mode()
    assert method.inhibit_cookie == fake_cookie


@pytest.mark.parametrize(
    "method_cls, flag",
    [
        (GnomeSessionManagerNoSuspend, GnomeFlag.INHIBIT_SUSPEND),
        (GnomeSessionManagerNoIdle, GnomeFlag.INHIBIT_IDLE),
    ],
)
def test_gnome_exit_mode(method_cls, flag):
    class TestAdapter(DbusAdapter):
        def process(self, call):
            assert call.method == method_uninhibit
            assert call.args == {"inhibit_cookie": fake_cookie}

    # Test the method
    method = method_cls(CallProcessor(dbus_adapter=TestAdapter))
    method.inhibit_cookie = fake_cookie

    # exiting mode unsets the inhibit_cookie
    method.exit_mode()
    assert method.inhibit_cookie is None
