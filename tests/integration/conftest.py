"""The tests in this folder test the D-Bus functionality. A real message bus 
is created with dbus-daemon in a subprocess."""

import logging
import multiprocessing as mp

import pytest
from testutils.dbus_service import DbusService
from testutils.privatebus import PrivateSessionBus

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def private_bus():
    """This is something that runs before any tests"""
    bus = PrivateSessionBus()
    bus_address = bus.start()
    logger.info("Initiated private bus: %s", bus_address)

    yield bus_address

    logger.info("Terminating private bus")
    bus.stop()


class SessionManager(DbusService):
    ...


def start_service(service_cls, bus_address, server_name, object_path, queue):
    service = service_cls(bus_address, queue)
    service.start(
        server_name=server_name,
        object_path=object_path,
    )


@pytest.fixture(scope="package", autouse=True)
def dbus_service(private_bus):
    """The DBus adapters are tested against a real DBus service using a private
    dbus-daemon. This fixture makes sure that a test service is available on
    the bus for tests.
    """
    logger.info("Initializing dbus_services")

    queue = mp.Queue()
    proc = mp.Process(
        target=start_service,
        kwargs=dict(
            service_cls=SessionManager,
            bus_address=private_bus,
            server_name="org.github.wakepy.TestManager",
            object_path="/org/github/wakepy/TestManager",
            queue=queue,
        ),
    )

    proc.start()
    # Wait until the dbus service is ready to receive messages. This is needed
    # as there is slight chance that the test try to connect to nonexisting
    # service, which will make the test fail randomly (but rarely) for no
    # apparent reason
    assert queue.get() == "ready"
    logger.info("Initialization of dbus_services ready")

    yield

    logger.info("Stopping dbus_services")
    proc.terminate()
    logger.info("Stopped dbus_services")
