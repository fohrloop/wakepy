import pytest

from wakepy.core.method import Method, PlatformName

# B, D, E
FIRST_MODE = "first_mode"
# A, F
SECOND_MODE = "second_mode"


@pytest.fixture(scope="function")
def provide_methods_different_platforms(monkeypatch):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method._method_registry", dict())

    class WindowsA(Method):
        name = "WinA"
        supported_platforms = (PlatformName.WINDOWS,)

    class WindowsB(Method):
        name = "WinB"
        supported_platforms = (PlatformName.WINDOWS,)

    class WindowsC(Method):
        name = "WinC"
        supported_platforms = (PlatformName.WINDOWS,)

    class LinuxA(Method):
        name = "LinuxA"
        supported_platforms = (PlatformName.LINUX,)

    class LinuxB(Method):
        name = "LinuxB"
        supported_platforms = (PlatformName.LINUX,)

    class LinuxC(Method):
        name = "LinuxC"
        supported_platforms = (PlatformName.LINUX,)

    class MultiPlatformA(Method):
        name = "multiA"
        supported_platforms = (
            PlatformName.LINUX,
            PlatformName.WINDOWS,
            PlatformName.MACOS,
        )


@pytest.fixture(scope="function")
def provide_methods_a_f(monkeypatch):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method._method_registry", dict())

    class MethodA(Method):
        name = "A"
        mode = SECOND_MODE

    class MethodB(Method):
        name = "B"
        mode = FIRST_MODE

    class MethodC(Method):
        name = "C"

    class MethodD(Method):
        name = "D"
        mode = FIRST_MODE

    class MethodE(Method):
        name = "E"
        mode = FIRST_MODE

    class MethodF(Method):
        name = "F"
        mode = SECOND_MODE
