"""Test D-bus adapters."""

import re
import struct
import sys

import pytest

if not sys.platform.lower().startswith("linux"):
    # D-Bus methods currently support only linux.
    pytest.skip(allow_module_level=True)

import jeepney
import pytest

from wakepy.core import DBusAddress, DBusMethod, DBusMethodCall
from wakepy.dbus_adapters.jeepney import JeepneyDBusAdapter

# For some unknown reason, when using jeepney, one will get a warning like
# this:
# ResourceWarning: unclosed <socket.socket fd=14, family=AddressFamily.AF_UNIX, type=SocketKind.SOCK_STREAM, proto=0, raddr=b'\x00/tmp/dbus-cTfPKAeBWk'>
# This is just ignored. It only triggers at *random* line, on random test when
# python does garbage collection.
#
# Ref1: https://docs.pytest.org/en/7.1.x/reference/reference.html#pytest-mark-filterwarnings
# Ref2: https://docs.pytest.org/en/7.1.x/reference/reference.html#globalvar-pytestmark
pytestmark = pytest.mark.filterwarnings(
    r"ignore:unclosed.*raddr=b'\\x00/tmp/dbus-.*:ResourceWarning"
)


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_numberadd(numberadd_method):
    adapter = JeepneyDBusAdapter()
    call = DBusMethodCall(numberadd_method, (2, 3))
    assert adapter.process(call) == (5,)


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_number_multiply(numbermultiply_method):
    adapter = JeepneyDBusAdapter()
    call = DBusMethodCall(numbermultiply_method, (-5, 3))
    assert adapter.process(call) == (-15,)


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_wrong_arguments(numbermultiply_method):
    adapter = JeepneyDBusAdapter()
    with pytest.raises(struct.error, match="required argument is not an intege"):
        # Bad input arg type
        adapter.process(DBusMethodCall(numbermultiply_method, (-5, "foo")))
    with pytest.raises(
        ValueError, match=re.escape("Expected args to have 2 items! (has: 3)")
    ):
        # Too many input args
        adapter.process(DBusMethodCall(numbermultiply_method, (-5, 3, 3)))


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_wrong_signature(calculator_service_addr):
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
        # The args are correct for the DBusMethod, but the DBusMethod is not
        # correct for the service (signature is wrong)
        adapter.process(DBusMethodCall(wrong_method, (-5, "sdaasd")))


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_nonexisting_method(calculator_service_addr):
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


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_wrong_service_definition(private_bus: str):
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
            "The name org.github.wakepy.WrongService was not provided by any .service "
            "files"
        ),
    ):
        adapter.process(DBusMethodCall(wrong_method, (-5, 2)))


@pytest.mark.usefixtures("dbus_string_operation_service")
def test_jeepney_dbus_adapter_string_shorten(string_shorten_method):
    # The service shortens a string to a given number of characters and tells
    # how many characters were dropped out.
    adapter = JeepneyDBusAdapter()
    call = DBusMethodCall(string_shorten_method, ("cat pinky", 3))
    assert adapter.process(call) == ("cat", 6)
