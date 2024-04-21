import pytest

from wakepy import DBusAdapter
from wakepy.core.registry import register_method
from wakepy.methods._testing import WakepyFakeSuccess


class TestDBusAdapter(DBusAdapter):
    """A fake dbus adapter used in tests"""


@pytest.fixture(scope="session")
def fake_dbus_adapter():
    return TestDBusAdapter


class TestUtils:
    """Any functions needed to be "imported" anywhere from any tests. Available
    as a fixture called `testutils`.
    """

    @staticmethod
    def empty_method_registry(monkeypatch, fake_success=False):
        """
        Make the method registry empty for duration of a test. Keep
        the WakepyFakeSuccess method in the registry. and optionally set the
        WAKEPY_FAKE_SUCCESS flag to a truthy value (if `fake_success` is True).
        """
        monkeypatch.setattr("wakepy.core.registry._method_registry", (dict()))
        # The fake method should always be part of the registry.
        register_method(WakepyFakeSuccess)

        if fake_success:
            monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "1")


@pytest.fixture(scope="session")
def testutils():
    return TestUtils


@pytest.fixture(scope="function", name="empty_method_registry")
def empty_method_registry_fixture(monkeypatch):
    TestUtils.empty_method_registry(monkeypatch)
