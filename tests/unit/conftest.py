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
    def empty_method_registry(monkeypatch):
        """
        Make the method registry empty for duration of a test. Keep
        the WakepyFakeSuccess method in the registry.
        """
        monkeypatch.setattr("wakepy.core.registry._method_registry", (dict()))
        # The fake method should always be part of the registry.
        register_method(WakepyFakeSuccess)


@pytest.fixture(scope="session")
def testutils():
    return TestUtils


@pytest.fixture(scope="function", name="empty_method_registry")
def empty_method_registry_fixture(monkeypatch):
    TestUtils.empty_method_registry(monkeypatch)


@pytest.fixture(scope="function", name="WAKEPY_FAKE_SUCCESS_eq_1")
def _wakepy_fake_success_fixture(monkeypatch):
    monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "1")
