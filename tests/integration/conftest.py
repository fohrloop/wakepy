"""The DBus adapters are tested against real DBus service(s). This module
provides the services as fixtures. The services run in separate threads.
"""

import logging
import subprocess
import sys

import pytest

if sys.platform.lower().startswith("linux"):
    from dbus_service import DBusService, start_dbus_service
else:
    DBusService = None
    start_dbus_service = None

from wakepy.core import DBusAddress, DBusMethod

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def private_bus():
    """A real, private message bus (dbus-daemon) instance which can be used
    to test dbus adapters. You can see the bus running with

    $ ps -x | grep dbus-daemon | grep -v grep | grep dbus-daemon

    It is listed as something like

        11150 pts/0    S      0:00 dbus-daemon --session --print-address

    (includes the _start_cmd which is defined below)
    """

    _start_cmd = "dbus-daemon --session --print-address"

    p = subprocess.Popen(
        _start_cmd.split(),
        stdout=subprocess.PIPE,
        shell=False,
        env={"DBUS_VERBOSE": "1"},
    )

    bus_address = p.stdout.readline().decode("utf-8").strip()

    logger.info("Initiated private bus: %s", bus_address)

    yield bus_address

    logger.info("Terminating private bus")
    p.terminate()


@pytest.fixture(scope="session")
def string_operation_service_addr(private_bus: str) -> DBusAddress:
    return DBusAddress(
        bus=private_bus,
        service="org.github.wakepy.TestStringOperationService",
        path="/org/github/wakepy/TestStringOperationService",
        interface="org.github.wakepy.TestStringOperationService",  # TODO: simplify
    )


@pytest.fixture(scope="session")
def calculator_service_addr(private_bus: str) -> DBusAddress:
    return DBusAddress(
        bus=private_bus,
        service="org.github.wakepy.TestCalculatorService",
        path="/org/github/wakepy/TestCalculatorService",
        interface="org.github.wakepy.TestCalculatorService",  # TODO: simplify
    )


@pytest.fixture(scope="session")
def numberadd_method(calculator_service_addr: DBusAddress) -> DBusMethod:
    return DBusMethod(
        name="SimpleNumberAdd",
        signature="uu",
        params=("first_number", "second_number"),
        output_signature="u",
        output_params=("result",),
    ).of(calculator_service_addr)


@pytest.fixture(scope="session")
def numbermultiply_method(calculator_service_addr: DBusAddress) -> DBusMethod:
    return DBusMethod(
        name="SimpleNumberMultiply",
        signature="ii",
        params=("first_number", "second_number"),
        output_signature="i",
        output_params=("result",),
    ).of(calculator_service_addr)


@pytest.fixture(scope="session")
def string_shorten_method(string_operation_service_addr: DBusAddress) -> DBusMethod:
    return DBusMethod(
        name="ShortenToNChars",
        signature="su",
        params=("the_string", "max_chars"),
        output_signature="su",
        output_params=("shortened_string", "n_removed_chars"),
    ).of(string_operation_service_addr)


@pytest.fixture(scope="session")
def dbus_calculator_service(
    calculator_service_addr: DBusAddress,
    numberadd_method: DBusMethod,
    numbermultiply_method: DBusMethod,
    private_bus: str,
):
    """Provides a DBus service called org.github.wakepy.TestCalculatorService
    in the session bus"""

    class TestCalculatorService(DBusService):
        addr = calculator_service_addr

        def handle_method(self, method: str, args):
            if method == numberadd_method.name:
                res = args[0] + args[1]
                return numberadd_method.output_signature, (res,)
            elif method == numbermultiply_method.name:
                res = args[0] * args[1]
                return numbermultiply_method.output_signature, (res,)

    yield from start_dbus_service(TestCalculatorService, bus_address=private_bus)


@pytest.fixture(scope="session")
def dbus_string_operation_service(
    string_operation_service_addr: DBusAddress,
    string_shorten_method: DBusMethod,
    private_bus: str,
):
    """Provides a DBus service called org.github.wakepy.TestStringOperationService
    in the session bus"""

    class TestStringOperationService(DBusService):
        addr = string_operation_service_addr

        def handle_method(self, method: str, args):
            if method == string_shorten_method.name:
                string, max_chars = args[0], args[1]
                shortened_string = string[:max_chars]
                if len(shortened_string) < len(string):
                    n_removed = len(string) - len(shortened_string)
                else:
                    n_removed = 0
                return string_shorten_method.output_signature, (
                    shortened_string,
                    n_removed,
                )

    yield from start_dbus_service(TestStringOperationService, bus_address=private_bus)
