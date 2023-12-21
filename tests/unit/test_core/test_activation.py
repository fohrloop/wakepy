import re

import pytest
from testmethods import MethodIs, get_test_method_class

from wakepy.core.method import (
    Method,
    PlatformName,
    get_methods,
)

from wakepy.core.activation import caniuse_fails, get_platform_supported


@pytest.mark.usefixtures("provide_methods_different_platforms")
def test_get_platform_supported():
    WindowsA, LinuxA, MultiPlatformA = get_methods(["WinA", "LinuxA", "multiA"])

    # The windows method is only supported on windows
    assert get_platform_supported(WindowsA(), PlatformName.WINDOWS)
    assert not get_platform_supported(WindowsA(), PlatformName.LINUX)
    assert not get_platform_supported(WindowsA(), PlatformName.MACOS)

    # The linux method is only supported on linux
    assert get_platform_supported(LinuxA(), PlatformName.LINUX)
    assert not get_platform_supported(LinuxA(), PlatformName.WINDOWS)
    assert not get_platform_supported(LinuxA(), PlatformName.MACOS)

    # Case: Method that supports linux, windows and macOS
    assert get_platform_supported(MultiPlatformA(), PlatformName.LINUX)
    assert get_platform_supported(MultiPlatformA(), PlatformName.WINDOWS)
    assert get_platform_supported(MultiPlatformA(), PlatformName.MACOS)


@pytest.mark.parametrize(
    "params",
    [
        # True and None -> The check does not fail
        dict(caniuse=True, expected=(False, "")),
        dict(caniuse=None, expected=(False, "")),
        # If returning False, the check fails
        dict(caniuse=False, expected=(True, "")),
        # If returning a string, the check fails with a reason
        dict(caniuse="reason", expected=(True, "reason")),
        # If .caniuse() returns anything else than a string, that is silently
        # converted to a string, and the check fails.
        dict(caniuse=123, expected=(True, "123")),
    ],
)
def test_caniuse_fails(params):
    class SomeMethod(Method):
        def caniuse(self):
            return params["caniuse"]

    assert caniuse_fails(SomeMethod()) == params["expected"]
