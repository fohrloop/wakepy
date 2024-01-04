"""The DBus adapters are tested against real DBus service(s). This module 
provides the services as fixtures. The services run in separate threads.
"""

import logging
import threading
from typing import Type, Callable
import queue

import pytest
from testutils import DbusService


from wakepy.core import BusType, DbusAddress, DbusMethod


logger = logging.getLogger(__name__)

calculator_service_addr = DbusAddress(
    bus=BusType.SESSION,
    service="org.github.wakepy.CalculatorService",
    path="/org/github/wakepy/CalculatorService",
    interface="org.github.wakepy.CalculatorService",  # TODO: simplify
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


class CalculatorService(DbusService):
    addr = calculator_service_addr

    def handle_method(self, method: str, args):
        if method == _numberadd_method.name:
            res = args[0] + args[1]
            return _numberadd_method.output_signature, (res,)
        elif method == _numbermultiply_method.name:
            res = args[0] * args[1]
            return _numbermultiply_method.output_signature, (res,)


@pytest.fixture(scope="session")
def numberadd_method():
    return _numberadd_method


@pytest.fixture(scope="session")
def numbermultiply_method():
    return _numbermultiply_method


@pytest.fixture(scope="session")
def dbus_calculator_service():
    def start_service(
        service: Type[DbusService], queue_: queue.Queue, should_stop: Callable
    ):
        logger.info(f"Launching dbus service: {service.addr.service}")

        service_ = service(service.addr.bus, queue_, stop=should_stop)
        service_.start(
            server_name=service.addr.service,
            object_path=service.addr.path,
        )

    queue_ = queue.Queue()
    should_stop = False
    th = threading.Thread(
        target=start_service,
        kwargs=dict(
            service=CalculatorService, queue_=queue_, should_stop=lambda: should_stop
        ),
        daemon=True,
    )

    th.start()
    # Wait until the dbus service is ready to receive messages. This is needed
    # as there is slight chance that the test try to connect to nonexisting
    # service, which will make the test fail randomly (but rarely) for no
    # apparent reason
    assert queue_.get(timeout=2) == "ready"
    logger.info("Initialization of dbus_services ready")

    yield

    should_stop = True
    logger.info("Stopping dbus_services")
    th.join(1)
    if th.is_alive():
        raise Exception("Service did not stop!")
    logger.info("Stopped dbus_services")
