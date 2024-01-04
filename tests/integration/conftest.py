"""The DBus adapters are tested against real DBus service(s). This module 
provides the services as fixtures. The services run in separate threads.
"""

import logging
import queue
import threading
from typing import Callable, Type

import pytest
from testutils import DbusService

from wakepy.core import BusType, DbusAddress, DbusMethod

logger = logging.getLogger(__name__)

calculator_service_addr = DbusAddress(
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
).of(calculator_service_addr)

_numbermultiply_method = DbusMethod(
    name="SimpleNumberMultiply",
    signature="ii",
    params=("first_number", "second_number"),
    output_signature="i",
    output_params=("result",),
).of(calculator_service_addr)


class TestCalculatorService(DbusService):
    addr = calculator_service_addr

    def handle_method(self, method: str, args):
        if method == _numberadd_method.name:
            res = args[0] + args[1]
            return _numberadd_method.output_signature, (res,)
        elif method == _numbermultiply_method.name:
            res = args[0] * args[1]
            return _numbermultiply_method.output_signature, (res,)


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
    yield from _dbus_service(TestCalculatorService)


@pytest.fixture(scope="session")
def dbus_string_operation_service():
    """Provides a Dbus service called org.github.wakepy.TestStringOperationService
    in the session bus"""
    yield from _dbus_service(TestStringOperationService)


def _dbus_service(service_cls: Type[DbusService]):
    """Start a Dbus Service in a separate thread."""

    queue_ = queue.Queue()
    should_stop = False

    def start_service(
        service: Type[DbusService], queue_: queue.Queue, should_stop: Callable
    ):
        logger.info(f"Launching dbus service: {service.addr.service}")

        service_ = service(service.addr.bus, queue_, stop=should_stop)
        service_.start(
            server_name=service.addr.service,
            object_path=service.addr.path,
        )

    th = threading.Thread(
        target=start_service,
        kwargs=dict(
            service=service_cls, queue_=queue_, should_stop=lambda: should_stop
        ),
        daemon=True,
    )

    th.start()
    # Wait until the dbus service is ready to receive messages. This is needed
    # as there is slight chance that the test try to connect to nonexisting
    # service, which will make the test fail randomly (but rarely) for no
    # apparent reason
    assert queue_.get(timeout=2) == "ready"
    logger.info(f"Initialization of {service_cls.addr.service} ready")

    yield

    should_stop = True
    logger.info(f"Stopping {service_cls.addr.service}")
    th.join(1)
    if th.is_alive():
        raise Exception(f"Service {service_cls.addr.service} did not stop!")
    logger.info(f"Stopped {service_cls.addr.service}")
