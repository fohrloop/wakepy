import pytest

from wakepy import DbusAdapter


class TestDbusAdapter(DbusAdapter):
    """A fake dbus adapter used in tests"""


@pytest.fixture(scope="session")
def fake_dbus_adapter():
    return TestDbusAdapter
