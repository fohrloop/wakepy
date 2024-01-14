"""The DBus adapters are tested against real DBus service(s). This module 
provides the services as fixtures. The services run in separate threads.
"""

import pytest
from dbus_service import DbusService, start_dbus_service

from wakepy.core import BusType, DbusAddress, DbusMethod

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


@pytest.fixture(scope="session")
def dbus_calculator_service():
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

    yield from start_dbus_service(TestCalculatorService)


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
