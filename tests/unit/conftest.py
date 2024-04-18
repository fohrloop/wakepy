import pytest

from wakepy import DBusAdapter
from wakepy.core.registry import register_method
from wakepy.methods._fakesuccess import WakepyFakeSuccess


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
        Make the method registry empty for duration of a test. Optionally, keep
        the WakepyFakeSuccess method in the registry.
        """
        monkeypatch.setattr("wakepy.core.registry._method_registry", (dict()))
        if fake_success:
            register_method(WakepyFakeSuccess)
            monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "yes")


@pytest.fixture(scope="session")
def testutils():
    return TestUtils


@pytest.fixture(scope="function", name="empty_method_registry")
def empty_method_registry_fixture(monkeypatch):
    TestUtils.empty_method_registry(monkeypatch)
