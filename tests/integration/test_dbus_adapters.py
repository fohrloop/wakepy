"""Test D-bus adapters."""

import re
import struct

import pytest
import sys

if not sys.platform.lower().startswith("linux"):
    # D-Bus methods currently support only linux.
    pytest.skip(allow_module_level=True)

import jeepney
import pytest

from wakepy.core import BusType, DbusAddress, DbusMethod, DbusMethodCall
from wakepy.io.dbus.jeepney import JeepneyDbusAdapter


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_numberadd(numberadd_method):
    adapter = JeepneyDbusAdapter()
    call = DbusMethodCall(numberadd_method, (2, 3))
    assert adapter.process(call) == (5,)


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_number_multiply(numbermultiply_method):
    adapter = JeepneyDbusAdapter()
    call = DbusMethodCall(numbermultiply_method, (-5, 3))
    assert adapter.process(call) == (-15,)


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_wrong_arguments(numbermultiply_method):
    adapter = JeepneyDbusAdapter()
    with pytest.raises(struct.error, match="required argument is not an intege"):
        # Bad input arg type
        adapter.process(DbusMethodCall(numbermultiply_method, (-5, "foo")))
    with pytest.raises(
        ValueError, match=re.escape("Expected args to have 2 items! (has: 3)")
    ):
        # Too many input args
        adapter.process(DbusMethodCall(numbermultiply_method, (-5, 3, 3)))


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_wrong_signature(calculator_service_addr):
    wrong_method = DbusMethod(
        name="SimpleNumberMultiply",
        signature="is",  # this is wrong: should be "ii"
        params=("first_number", "second_number"),
        output_signature="i",
        output_params=("result",),
    ).of(calculator_service_addr)

    adapter = JeepneyDbusAdapter()
    with pytest.raises(
        jeepney.wrappers.DBusErrorResponse,
        match="org.github.wakepy.TestCalculatorService.Error.OtherError",
    ):
        # The args are correct for the DbusMethod, but the DbusMethod is not
        # correct for the service (signature is wrong)
        adapter.process(DbusMethodCall(wrong_method, (-5, "sdaasd")))


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_nonexisting_method(calculator_service_addr):
    non_existing_method = DbusMethod(
        name="ThisDoesNotExist",
        signature="ii",
        params=("first_number", "second_number"),
        output_signature="i",
        output_params=("result",),
    ).of(calculator_service_addr)
    adapter = JeepneyDbusAdapter()

    with pytest.raises(
        jeepney.wrappers.DBusErrorResponse,
        match="org.github.wakepy.TestCalculatorService.Error.NoMethod",
    ):
        # No such method: ThisDoesNotExist
        adapter.process(DbusMethodCall(non_existing_method, (-5, 2)))


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter_wrong_service_definition():
    adapter = JeepneyDbusAdapter()

    wrong_service_addr = DbusAddress(
        bus=BusType.SESSION,
        service="org.github.wakepy.WrongService",
        path="/org/github/wakepy/TestCalculatorService",
        interface="org.github.wakepy.TestCalculatorService",
    )
    wrong_method = DbusMethod(
        name="SimpleNumberMultiply",
        signature="ii",
        params=("first_number", "second_number"),
        output_signature="i",
        output_params=("result",),
    ).of(wrong_service_addr)

    # The args are correct for the DbusMethod, but the DbusMethod is not
    # correct for the service (signature is wrong)
    with pytest.raises(
        jeepney.wrappers.DBusErrorResponse,
        match=re.escape(
            "The name org.github.wakepy.WrongService was not provided by any .service "
            "files"
        ),
    ):
        adapter.process(DbusMethodCall(wrong_method, (-5, 2)))


@pytest.mark.usefixtures("dbus_string_operation_service")
def test_jeepney_dbus_adapter_string_shorten(string_shorten_method):
    # The service shortens a string to a given number of characters and tells
    # how many characters were dropped out.
    adapter = JeepneyDbusAdapter()
    call = DbusMethodCall(string_shorten_method, ("cat pinky", 3))
    assert adapter.process(call) == ("cat", 6)
