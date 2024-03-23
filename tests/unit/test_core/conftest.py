import pytest

from wakepy.core import DBusAddress, DBusMethod, Method, PlatformName

# B, D, E
FIRST_MODE = "first_mode"
# A, F
SECOND_MODE = "second_mode"


class TestMethod(Method):
    __test__ = False  # for pytest
    mode = "_test"


@pytest.fixture(scope="function")
def provide_methods_different_platforms(monkeypatch, testutils):
    testutils.empty_method_registry(monkeypatch)

    class WindowsA(TestMethod):
        name = "WinA"
        supported_platforms = (PlatformName.WINDOWS,)

    class WindowsB(TestMethod):
        name = "WinB"
        supported_platforms = (PlatformName.WINDOWS,)

    class WindowsC(TestMethod):
        name = "WinC"
        supported_platforms = (PlatformName.WINDOWS,)

    class LinuxA(TestMethod):
        name = "LinuxA"
        supported_platforms = (PlatformName.LINUX,)

    class LinuxB(TestMethod):
        name = "LinuxB"
        supported_platforms = (PlatformName.LINUX,)

    class LinuxC(TestMethod):
        name = "LinuxC"
        supported_platforms = (PlatformName.LINUX,)

    class MultiPlatformA(TestMethod):
        name = "multiA"
        supported_platforms = (
            PlatformName.LINUX,
            PlatformName.WINDOWS,
            PlatformName.MACOS,
        )


@pytest.fixture(scope="function")
def provide_methods_a_f(monkeypatch, testutils):
    testutils.empty_method_registry(monkeypatch)

    class MethodA(TestMethod):
        name = "A"
        mode = SECOND_MODE

    class MethodB(TestMethod):
        name = "B"
        mode = FIRST_MODE

    class MethodC(TestMethod):
        name = "C"

    class MethodD(TestMethod):
        name = "D"
        mode = FIRST_MODE

    class MethodE(TestMethod):
        name = "E"
        mode = FIRST_MODE

    class MethodF(TestMethod):
        name = "F"
        mode = SECOND_MODE


@pytest.fixture
def service():
    return DBusAddress(path="/foo", service="wakepy.foo", interface="/foo")


@pytest.fixture
def dbus_method(service: DBusAddress):
    return DBusMethod(
        name="test-method", signature="isi", params=("first", "second", "third")
    ).of(service)
