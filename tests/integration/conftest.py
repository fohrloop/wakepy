"""The DBus adapters are tested against real DBus service(s). This module 
provides the services as fixtures. The services run in separate threads.
"""

import logging
import os
import subprocess
import sys

import pytest

if sys.platform.lower().startswith("linux"):
    from dbus_service import DbusService, start_dbus_service
else:
    DbusService = None

    def start_dbus_service():
        return None


from wakepy.core import BusType, DbusAddress, DbusMethod

logger = logging.getLogger(__name__)

_calculator_service_addr = DbusAddress(
    bus=BusType.SESSION,
    service="org.github.wakepy.TestCalculatorService",
    path="/org/github/wakepy/TestCalculatorService",
    interface="org.github.wakepy.TestCalculatorService",  # TODO: simplify
)

_numberadd_method = DbusMethod(
    name="SimpleNumberAdd",
    signature="uu",
    params=("first_number", "second_number"),
    output_signature="u",
    output_params=("result",),
).of(_calculator_service_addr)

_numbermultiply_method = DbusMethod(
    name="SimpleNumberMultiply",
    signature="ii",
    params=("first_number", "second_number"),
    output_signature="i",
    output_params=("result",),
).of(_calculator_service_addr)


string_operation_service_addr = DbusAddress(
    bus=BusType.SESSION,
    service="org.github.wakepy.TestStringOperationService",
    path="/org/github/wakepy/TestStringOperationService",
    interface="org.github.wakepy.TestStringOperationService",  # TODO: simplify
)

_string_shorten_method = DbusMethod(
    name="ShortenToNChars",
    signature="su",
    params=("the_string", "max_chars"),
    output_signature="su",
    output_params=("shortened_string", "n_removed_chars"),
).of(string_operation_service_addr)


@pytest.fixture(scope="session")
def calculator_service_addr():
    return _calculator_service_addr


@pytest.fixture(scope="session")
def numberadd_method():
    return _numberadd_method


@pytest.fixture(scope="session")
def numbermultiply_method():
    return _numbermultiply_method


@pytest.fixture(scope="session")
def string_shorten_method():
    return _string_shorten_method


@pytest.fixture(scope="session", autouse=True)
def private_bus():
    """A real, private message bus (dbus-daemon) instance which can be used
    to test dbus adapters. You can see the bus running with

    $ ps -x | grep dbus-daemon | grep -v grep | grep dbus-daemon

    It is listed as `PrivateSessionBus._start_cmd`  (e.g. "dbus-daemon
    --session --print-address")
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

    os.environ["DBUS_SESSION_BUS_ADDRESS"] = bus_address

    yield bus_address

    logger.info("Terminating private bus")
    p.terminate()


@pytest.fixture(scope="session")
def dbus_calculator_service(private_bus: str):
    """Provides a Dbus service called org.github.wakepy.TestCalculatorService
    in the session bus"""

    class TestCalculatorService(DbusService):
        addr = _calculator_service_addr

        def handle_method(self, method: str, args):
            if method == _numberadd_method.name:
                res = args[0] + args[1]
                return _numberadd_method.output_signature, (res,)
            elif method == _numbermultiply_method.name:
                res = args[0] * args[1]
                return _numbermultiply_method.output_signature, (res,)

    yield from start_dbus_service(TestCalculatorService, bus_address=private_bus)


@pytest.fixture(scope="session")
def dbus_string_operation_service():
    """Provides a Dbus service called org.github.wakepy.TestStringOperationService
    in the session bus"""

    class TestStringOperationService(DbusService):
        addr = string_operation_service_addr

        def handle_method(self, method: str, args):
            if method == _string_shorten_method.name:
                string, max_chars = args[0], args[1]
                shortened_string = string[:max_chars]
                if len(shortened_string) < len(string):
                    n_removed = len(string) - len(shortened_string)
                else:
                    n_removed = 0
                return _string_shorten_method.output_signature, (
                    shortened_string,
                    n_removed,
                )

    yield from start_dbus_service(TestStringOperationService)
