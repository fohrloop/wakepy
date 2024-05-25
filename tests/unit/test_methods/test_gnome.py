"""This module tests the GNOME specific methods.

These tests do *not* use IO / real or fake DBus calls. Instead, a special dbus
adapter is used which simply asserts the Call objects and returns what we
would expect from a dbus service."""

import re

import pytest

from wakepy.core.dbus import BusType, DBusAdapter, DBusAddress, DBusMethod
from wakepy.methods.gnome import (
    GnomeFlag,
    GnomeSessionManagerNoIdle,
    GnomeSessionManagerNoSuspend,
)

session_manager = DBusAddress(
    bus=BusType.SESSION,
    service="org.gnome.SessionManager",
    path="/org/gnome/SessionManager",
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
    method_inhibit = DBusMethod(
        name="Inhibit",
        signature="susu",
        params=("app_id", "toplevel_xid", "reason", "flags"),
        output_signature="u",
        output_params=("inhibit_cookie",),
    ).of(session_manager)

    class TestAdapter(DBusAdapter):
        def process(self, call):
            assert call.method == method_inhibit
            assert call.get_kwargs() == {
                "app_id": "wakepy",
                "toplevel_xid": 42,
                "reason": "wakelock active",
                "flags": flag,
            }

            return (fake_cookie,)

    method = method_cls(dbus_adapter=TestAdapter())
    assert method.inhibit_cookie is None

    # Act
    enter_retval = method.enter_mode()

    # Assert
    assert enter_retval is None
    # Entering mode sets a inhibit_cookie to value returned by the DBusAdapter
    assert method.inhibit_cookie == fake_cookie


@pytest.mark.parametrize(
    "method_cls",
    [GnomeSessionManagerNoSuspend, GnomeSessionManagerNoIdle],
)
def test_gnome_exit_mode(method_cls):
    # Arrange
    method_uninhibit = DBusMethod(
        name="Uninhibit",
        signature="u",
        params=("inhibit_cookie",),
    ).of(session_manager)

    class TestAdapter(DBusAdapter):
        def process(self, call):
            assert call.method == method_uninhibit
            assert call.get_kwargs() == {"inhibit_cookie": fake_cookie}

    method = method_cls(dbus_adapter=TestAdapter())
    method.inhibit_cookie = fake_cookie

    # Act
    exit_retval = method.exit_mode()

    # Assert
    assert exit_retval is None
    # exiting mode unsets the inhibit_cookie
    assert method.inhibit_cookie is None


@pytest.mark.parametrize(
    "method_cls",
    [GnomeSessionManagerNoSuspend, GnomeSessionManagerNoIdle],
)
def test_gnome_exit_before_enter(method_cls):
    method = method_cls(dbus_adapter=DBusAdapter())
    assert method.inhibit_cookie is None
    assert method.exit_mode() is None


@pytest.mark.parametrize(
    "method_cls",
    [GnomeSessionManagerNoSuspend, GnomeSessionManagerNoIdle],
)
def test_with_dbus_adapter_which_returns_none(method_cls):
    class BadAdapterReturnNone(DBusAdapter):
        def process(self, _):
            return None

    method = method_cls(dbus_adapter=BadAdapterReturnNone())

    with pytest.raises(
        RuntimeError,
        match=re.escape("Could not get inhibit cookie from org.gnome.SessionManager"),
    ):
        assert method.enter_mode() is False
