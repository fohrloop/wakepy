from wakepy.core import BusType, DbusAddress, DbusMethod, DbusMethodCall
from wakepy.io.dbus.jeepney import JeepneyDbusAdapter

calculator_service = DbusAddress(
    bus=BusType.SESSION,
    service="org.github.wakepy.CalculatorService",
    path="/org/github/wakepy/CalculatorService",
    interface="org.github.wakepy.CalculatorService",  # TODO: simplify
)

numberadd_method = DbusMethod(
    name="SimpleNumberAdd",
    signature="uu",
    params=("first_number", "second_number"),
    output_signature="u",
    output_params=("result",),
).of(calculator_service)


def test_jeepney_dbus_adapter():
    adapter = JeepneyDbusAdapter()
    call = DbusMethodCall(numberadd_method, (2, 3))
    assert adapter.process(call) == 5
