"""This module tests the Freedesktop.org specific methods.

These tests do *not* use IO / real or fake DBus calls. Instead, a special dbus
adapter is used which simply asserts the Call objects and returns what we
would expect from a dbus service."""

import re

import pytest

from wakepy.core.dbus import BusType, DBusAdapter, DBusAddress, DBusMethod
from wakepy.methods.freedesktop import (
    FreedesktopPowerManagementInhibit,
    FreedesktopScreenSaverInhibit,
)

screen_saver = DBusAddress(
    bus=BusType.SESSION,
    service="org.freedesktop.ScreenSaver",
    path="/org/freedesktop/ScreenSaver",
    interface="org.freedesktop.ScreenSaver",
)

power_management = DBusAddress(
    bus=BusType.SESSION,
    service="org.freedesktop.PowerManagement",
    path="/org/freedesktop/PowerManagement/Inhibit",
    interface="org.freedesktop.PowerManagement.Inhibit",
)

fake_cookie = 75848243423


def get_test_dbus_adapter(process) -> DBusAdapter:
    class TestAdapter(DBusAdapter):

        def process(self, call):
            return process(call)

    return TestAdapter()


class TestFreedesktopEnterMode:

    @pytest.mark.parametrize(
        "method_cls, dbus_address",
        [
            (FreedesktopScreenSaverInhibit, screen_saver),
            (FreedesktopPowerManagementInhibit, power_management),
        ],
    )
    def test_success(self, method_cls, dbus_address: DBusAddress):

        method_inhibit = DBusMethod(
            name="Inhibit",
            signature="ss",
            params=("application_name", "reason_for_inhibit"),
            output_signature="u",
            output_params=("cookie",),
        )

        def process(call):
            assert call.method == method_inhibit.of(dbus_address)
            assert call.get_kwargs() == {
                "application_name": "wakepy",
                "reason_for_inhibit": "wakelock active",
            }

            return (fake_cookie,)

        method = method_cls(dbus_adapter=get_test_dbus_adapter(process))
        # At the start, there is no inhibit cookie.
        assert method.inhibit_cookie is None

        # Act
        enter_retval = method.enter_mode()

        # Assert
        assert enter_retval is None
        # Entering mode sets a inhibit_cookie to value returned by the
        # DBusAdapter
        assert method.inhibit_cookie == fake_cookie

    @pytest.mark.parametrize(
        "method_cls",
        [FreedesktopScreenSaverInhibit, FreedesktopPowerManagementInhibit],
    )
    def test_with_dbus_adapter_which_returns_none(self, method_cls):

        def process(_):
            return None

        method = method_cls(dbus_adapter=get_test_dbus_adapter(process))

        with pytest.raises(
            RuntimeError,
            match=re.escape(f"Could not get inhibit cookie from {method_cls.name}"),
        ):
            assert method.enter_mode() is False


class TestFreedesktopExitMode:

    @pytest.mark.parametrize(
        "method_cls, dbus_address",
        [
            (FreedesktopScreenSaverInhibit, screen_saver),
            (FreedesktopPowerManagementInhibit, power_management),
        ],
    )
    def test_successful_exit(self, method_cls, dbus_address: DBusAddress):
        # Arrange

        method_uninhibit = DBusMethod(
            name="UnInhibit",
            signature="u",
            params=("cookie",),
        ).of(dbus_address)

        def process(call):
            assert call.method == method_uninhibit
            assert call.get_kwargs() == {"cookie": fake_cookie}

        method = method_cls(dbus_adapter=get_test_dbus_adapter(process))
        method.inhibit_cookie = fake_cookie

        # Act
        exit_retval = method.exit_mode()

        # Assert
        assert exit_retval is None
        # exiting mode unsets the inhibit_cookie
        assert method.inhibit_cookie is None

    @pytest.mark.parametrize(
        "method_cls",
        [FreedesktopScreenSaverInhibit, FreedesktopPowerManagementInhibit],
    )
    def test_screensaver_exit_before_enter(self, method_cls):
        method = method_cls(dbus_adapter=DBusAdapter())
        assert method.inhibit_cookie is None
        assert method.exit_mode() is None
