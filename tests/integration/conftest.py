import logging
import multiprocessing as mp

import pytest
from testutils import DbusService

logger = logging.getLogger(__name__)


# TODO: Make this better somehow?
@pytest.fixture(scope="package", autouse=True)
def dbus_service():
    """The DBus adapters are tested against a real DBus service using a private
    dbus-daemon. This fixture makes sure that a test service is available on
    the bus for tests.
    """
    logger.info("Initializing dbus_services")

    def start_service(
        service_cls, server_name, object_path, queue, bus_address="SESSION"
    ):
        service = service_cls(bus_address, queue)
        service.start(
            server_name=server_name,
            object_path=object_path,
        )

    queue = mp.Queue()
    proc = mp.Process(
        target=start_service,
        kwargs=dict(
            service_cls=DbusService,
            server_name="org.github.wakepy.CalculatorService",
            object_path="/org/github/wakepy/CalculatorService",
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
