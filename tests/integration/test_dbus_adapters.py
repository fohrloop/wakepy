import pytest

from wakepy.core import DbusMethodCall
from wakepy.io.dbus.jeepney import JeepneyDbusAdapter


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter(numberadd_method):
    adapter = JeepneyDbusAdapter()
    call = DbusMethodCall(numberadd_method, (2, 3))
    assert adapter.process(call) == (5,)


@pytest.mark.usefixtures("dbus_calculator_service")
def test_jeepney_dbus_adapter(numbermultiply_method):
    adapter = JeepneyDbusAdapter()
    call = DbusMethodCall(numbermultiply_method, (-5, 3))
    assert adapter.process(call) == (-15,)
