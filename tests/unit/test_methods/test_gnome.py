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


fake_cookie = 75848243423


@pytest.mark.parametrize(
    "method_cls, flag",
    [
        (GnomeSessionManagerNoSuspend, GnomeFlag.INHIBIT_SUSPEND),
        (GnomeSessionManagerNoIdle, GnomeFlag.INHIBIT_IDLE),
    ],
)
def test_gnome_enter_mode(method_cls, flag):
    # Arrange
    method_inhibit = DbusMethod(
        name="Inhibit",
        signature="susu",
        params=("app_id", "toplevel_xid", "reason", "flags"),
        output_signature="u",
        output_params=("inhibit_cookie",),
    ).of(session_manager)

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

    method = method_cls(CallProcessor(dbus_adapter=TestAdapter))
    assert method.inhibit_cookie is None

    # Act
    method.enter_mode()

    # Assert
    # Entering mode sets a inhibit_cookie to value returned by the DbusAdapter
    assert method.inhibit_cookie == fake_cookie


@pytest.mark.parametrize(
    "method_cls",
    [GnomeSessionManagerNoSuspend, GnomeSessionManagerNoIdle],
)
def test_gnome_exit_mode(method_cls):
    # Arrange
    method_uninhibit = DbusMethod(
        name="UnInhibit",
        signature="u",
        params=("inhibit_cookie",),
    ).of(session_manager)

    class TestAdapter(DbusAdapter):
        def process(self, call):
            assert call.method == method_uninhibit
            assert call.args == {"inhibit_cookie": fake_cookie}

    method = method_cls(CallProcessor(dbus_adapter=TestAdapter))
    method.inhibit_cookie = fake_cookie

    # Act
    method.exit_mode()

    # Assert
    # exiting mode unsets the inhibit_cookie
    assert method.inhibit_cookie is None


@pytest.mark.parametrize(
    "method_cls",
    [GnomeSessionManagerNoSuspend, GnomeSessionManagerNoIdle],
)
def test_gnome_exit_before_enter(method_cls):
    method = method_cls(CallProcessor(dbus_adapter=DbusAdapter))
    assert method.inhibit_cookie is None
    with pytest.raises(RuntimeError, match="Cannot exit before entering"):
        method.exit_mode()
