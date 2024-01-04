import pytest

from wakepy.core import DbusMethodCall
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


@pytest.mark.usefixtures("dbus_string_operation_service")
def test_jeepney_dbus_adapter_string_shorten(string_shorten_method):
    # The service shortens a string to a given number of characters and tells
    # how many characters were dropped out.
    adapter = JeepneyDbusAdapter()
    call = DbusMethodCall(string_shorten_method, ("cat pinky", 3))
    assert adapter.process(call) == ("cat", 6)
