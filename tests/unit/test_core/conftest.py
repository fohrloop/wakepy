import pytest

from tests.unit.test_core.testmethods import TestMethod
from wakepy.core import DBusAddress, DBusMethod, Method, PlatformType
from wakepy.core.heartbeat import Heartbeat


@pytest.fixture
def heartbeat1(method1: Method):
    """Well behaving Heartbeat instance"""
    return Heartbeat(method1)


@pytest.fixture
def heartbeat2_bad(method1: Method):
    """Bad Heartbeat instance. Returns a bad value."""

    class BadHeartbeat(Heartbeat):
        def stop(self):
            return "Bad value"

    return BadHeartbeat(method1)


@pytest.fixture(scope="function")
def provide_methods_different_platforms(monkeypatch, testutils):
    testutils.empty_method_registry(monkeypatch)

    class WindowsA(TestMethod):
        name = "WinA"
        supported_platforms = (PlatformType.WINDOWS,)

    class WindowsB(TestMethod):
        name = "WinB"
        supported_platforms = (PlatformType.WINDOWS,)

    class WindowsC(TestMethod):
        name = "WinC"
        supported_platforms = (PlatformType.WINDOWS,)

    class LinuxA(TestMethod):
        name = "LinuxA"
        supported_platforms = (PlatformType.LINUX,)

    class LinuxB(TestMethod):
        name = "LinuxB"
        supported_platforms = (PlatformType.LINUX,)

    class LinuxC(TestMethod):
        name = "LinuxC"
        supported_platforms = (PlatformType.LINUX,)

    class MultiPlatformA(TestMethod):
        name = "multiA"
        supported_platforms = (
            PlatformType.LINUX,
            PlatformType.WINDOWS,
            PlatformType.MACOS,
        )


@pytest.fixture(scope="function")
def provide_methods_a_f(monkeypatch, testutils):
    testutils.empty_method_registry(monkeypatch)
    # B, D, E
    FIRST_MODE = "first_mode"
    # A, F
    SECOND_MODE = "second_mode"

    class MethodA(TestMethod):
        name = "A"
        mode_name = SECOND_MODE

    class MethodB(TestMethod):
        name = "B"
        mode_name = FIRST_MODE

    class MethodC(TestMethod):
        name = "C"

    class MethodD(TestMethod):
        name = "D"
        mode_name = FIRST_MODE

    class MethodE(TestMethod):
        name = "E"
        mode_name = FIRST_MODE

    class MethodF(TestMethod):
        name = "F"
        mode_name = SECOND_MODE


@pytest.fixture
def service():
    return DBusAddress(path="/foo", service="wakepy.foo", interface="/foo")


@pytest.fixture
def dbus_method(service: DBusAddress):
    return DBusMethod(
        name="test-method", signature="isi", params=("first", "second", "third")
    ).of(service)
