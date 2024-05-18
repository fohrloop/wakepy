"""Test D-bus adapters using a real dbus-daemon service."""

import re
import struct
import sys
from unittest.mock import patch

import pytest

if not sys.platform.lower().startswith("linux"):
    # D-Bus methods currently support only linux.
    pytest.skip(allow_module_level=True)

import jeepney
import pytest

from wakepy import JeepneyDBusAdapter
from wakepy.core import DBusAddress, DBusMethod, DBusMethodCall
from wakepy.dbus_adapters.jeepney import DBusNotFoundError

# For some unknown reason, when using jeepney, one will get a warning like
# this:
# ResourceWarning: unclosed <socket.socket fd=14, family=AddressFamily.AF_UNIX, type=SocketKind.SOCK_STREAM, proto=0, raddr=b'\x00/tmp/dbus-cTfPKAeBWk'> # noqa: E501, W505
# This is just ignored. It only triggers at *random* line, on random test when
# python does garbage collection.
#
# Ref1: https://docs.pytest.org/en/7.1.x/reference/reference.html#pytest-mark-filterwarnings
# Ref2: https://docs.pytest.org/en/7.1.x/reference/reference.html#globalvar-pytestmark
pytestmark = pytest.mark.filterwarnings(
    r"ignore:unclosed.*raddr=b'\\x00/tmp/dbus-.*:ResourceWarning"
)


@pytest.mark.usefixtures("dbus_calculator_service")
class TestJeepneyCalculatorService:

    def test_numberadd(self, numberadd_method):
        adapter = JeepneyDBusAdapter()
        call = DBusMethodCall(numberadd_method, (2, 3))
        assert adapter.process(call) == (5,)

    def test_number_multiply(self, numbermultiply_method):
        adapter = JeepneyDBusAdapter()
        call = DBusMethodCall(numbermultiply_method, (-5, 3))
        assert adapter.process(call) == (-15,)

    def test_multiply_with_wrong_arguments(self, numbermultiply_method):
        adapter = JeepneyDBusAdapter()
        with pytest.raises(struct.error, match="required argument is not an intege"):
            # Bad input arg type
            adapter.process(DBusMethodCall(numbermultiply_method, (-5, "foo")))
        with pytest.raises(
            ValueError, match=re.escape("Expected args to have 2 items! (has: 3)")
        ):
            # Too many input args
            adapter.process(DBusMethodCall(numbermultiply_method, (-5, 3, 3)))

    def test_wrong_signature(self, calculator_service_addr):
        wrong_method = DBusMethod(
            name="SimpleNumberMultiply",
            signature="is",  # this is wrong: should be "ii"
            params=("first_number", "second_number"),
            output_signature="i",
            output_params=("result",),
        ).of(calculator_service_addr)

        adapter = JeepneyDBusAdapter()
        with pytest.raises(
            jeepney.wrappers.DBusErrorResponse,
            match="org.github.wakepy.TestCalculatorService.Error.OtherError",
        ):
            # The args are correct for the DBusMethod, but the DBusMethod is
            # not correct for the service (signature is wrong)
            adapter.process(DBusMethodCall(wrong_method, (-5, "sdaasd")))

    def test_nonexisting_method(self, calculator_service_addr):
        non_existing_method = DBusMethod(
            name="ThisDoesNotExist",
            signature="ii",
            params=("first_number", "second_number"),
            output_signature="i",
            output_params=("result",),
        ).of(calculator_service_addr)
        adapter = JeepneyDBusAdapter()

        with pytest.raises(
            jeepney.wrappers.DBusErrorResponse,
            match="org.github.wakepy.TestCalculatorService.Error.NoMethod",
        ):
            # No such method: ThisDoesNotExist
            adapter.process(DBusMethodCall(non_existing_method, (-5, 2)))

    def test_wrong_service_definition(self, private_bus: str):
        adapter = JeepneyDBusAdapter()

        wrong_service_addr = DBusAddress(
            bus=private_bus,
            service="org.github.wakepy.WrongService",
            path="/org/github/wakepy/TestCalculatorService",
            interface="org.github.wakepy.TestCalculatorService",
        )
        wrong_method = DBusMethod(
            name="SimpleNumberMultiply",
            signature="ii",
            params=("first_number", "second_number"),
            output_signature="i",
            output_params=("result",),
        ).of(wrong_service_addr)

        # The args are correct for the DBusMethod, but the DBusMethod is not
        # correct for the service (signature is wrong)
        with pytest.raises(
            jeepney.wrappers.DBusErrorResponse,
            match=re.escape(
                "The name org.github.wakepy.WrongService was not provided by any "
                ".service files"
            ),
        ):
            adapter.process(DBusMethodCall(wrong_method, (-5, 2)))


@pytest.mark.usefixtures("dbus_string_operation_service")
class TestJeepneyStringOperationService:

    def test_jeepney_dbus_adapter_string_shorten(self, string_shorten_method):
        # The service shortens a string to a given number of characters and
        # tells how many characters were dropped out.
        adapter = JeepneyDBusAdapter()
        call = DBusMethodCall(string_shorten_method, ("cat pinky", 3))
        assert adapter.process(call) == ("cat", 6)


class TestFailuresOnConnectionCreation:
    adapter = JeepneyDBusAdapter()

    @pytest.fixture(autouse=True)
    def _create_call(self, string_shorten_method):
        # This could be any valid call.
        self.call = DBusMethodCall(string_shorten_method, ("1", 2))

    @staticmethod
    def failing_open_dbus_connection(bus):
        raise KeyError("Could not find DBUS_SESSION_BUS_ADDRESS")

    @staticmethod
    def failing_open_dbus_connection_random_reason(bus):
        raise KeyError("Some other reason")

    def test_dbus_session_bus_keyerror_on_connection_creation(
        self,
    ):
        # The open_dbus_connection may sometimes raise KeyError when
        # DBUS_SESSION_BUS_ADDRESS env var is not set. This test that case.

        with patch(
            "wakepy.dbus_adapters.jeepney.open_dbus_connection",
            self.failing_open_dbus_connection,
        ):
            with pytest.raises(
                DBusNotFoundError,
                match="The environment variable DBUS_SESSION_BUS_ADDRESS is not set!",
            ):
                self.adapter.process(self.call)

    def test_random_keyerror_on_connection_creation(
        self,
    ):
        with patch(
            "wakepy.dbus_adapters.jeepney.open_dbus_connection",
            self.failing_open_dbus_connection_random_reason,
        ):
            with pytest.raises(
                KeyError,
                match="Some other reason",
            ):
                self.adapter.process(self.call)


class TestJeepneyDbusAdapter:

    def test_close_connections(self, private_bus: str):
        adapter = JeepneyDBusAdapter()
        con = adapter._get_connection(private_bus)
        # There seems to be no other way checking that the connection is
        # active..?
        assert not con.sock._closed  # type: ignore[attr-defined]
        adapter.close_connections()
        assert con.sock._closed  # type: ignore[attr-defined]

    def test_adapter_caching(self, private_bus: str):
        adapter = JeepneyDBusAdapter()
        con = adapter._get_connection(private_bus)

        # Call again with same bus name -> get same (cached) connection.
        assert adapter._get_connection(private_bus) is con
