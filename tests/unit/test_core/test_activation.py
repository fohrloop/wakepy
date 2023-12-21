import re

import pytest
from testmethods import MethodIs, get_test_method_class, iterate_test_methods

from wakepy.core.method import (
    Method,
    PlatformName,
    get_methods,
)

from wakepy.core.activation import (
    caniuse_fails,
    get_platform_supported,
    try_enter_and_heartbeat,
)

"""
TABLE 1
Test table for try_enter_and_heartbeat. Methods are {enter_mode}{heartbeat}
where {enter_mode} and {heartbeat} are

M: Missing implementation
F: Failed attempt (with or without message)
S: Succesful attempt

Methods   Expected result
-------   ---------------------------------------------------------
1)  F*    Return Fail + enter_mode error message

2)  MM    Raise Exception -- the Method is faulty.
3)  MF    Return Fail + heartbeat error message
4)  MS    Return Success + heartbeat time

5)  SM    Return Success
6)  SF    Return Fail + heartbeat error message + call exit_mode()
7)  SS    Return Success + heartbeat time
"""


def test_try_enter_and_heartbeat_failing_enter_mode():
    """Tests 1) F* from TABLE 1 when enter_mode returns False"""
    for method in iterate_test_methods(
        enter_mode=[MethodIs.FAILING],
        heartbeat=MethodIs,
        exit_mode=MethodIs,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting
        # * entering to FAIL (False)
        # * empty error message (''), as not using FAILING_MESSAGE
        # * No heartbeat_call_time (None)
        assert res == (False, "", None)


def test_try_enter_and_heartbeat_failing_enter_mode_with_error_message():
    """Tests 1) F* from TABLE 1 when enter_mode returns a string (error message)"""
    for method in iterate_test_methods(
        enter_mode=[MethodIs.FAILING_MESSAGE],
        heartbeat=MethodIs,
        exit_mode=MethodIs,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting
        # * entering to FAIL (False)
        # * error message ('failure_reason'), as using FAILING_MESSAGE
        # * No heartbeat_call_time (None)
        assert res == (False, "failure_reason", None)


def test_try_enter_and_heartbeat_missing_enter_mode_and_heartbeat():
    """Tests 2) MM from TABLE 1; missing both enter_mode and heartbeat"""
    for method in iterate_test_methods(
        enter_mode=[MethodIs.MISSING],
        heartbeat=[MethodIs.MISSING],
        exit_mode=MethodIs,
    ):
        # Expecting an error as missing enter_mode and heartbeat
        with pytest.raises(
            RuntimeError,
            match=re.escape(
                f"Method {method.__class__.__name__} ({method.name}) is not properly defined! Missing implementation for both, enter_mode() and heartbeat()!"
            ),
        ):
            try_enter_and_heartbeat(method)


def test_try_enter_and_heartbeat_enter_mode_missing_heartbeat_failing():
    """Tests 3) MF from TABLE 1; enter_mode missing and heartbeat failing"""
    for method in iterate_test_methods(
        enter_mode=[MethodIs.MISSING],
        heartbeat=[MethodIs.FAILING],
        exit_mode=MethodIs,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting
        # * heartbeat to FAIL (-> False)
        # * No error message (''), as using FAILING
        # * No heartbeat_call_time (None)
        assert res == (False, "", None)

    for method in iterate_test_methods(
        enter_mode=[MethodIs.MISSING],
        heartbeat=[MethodIs.FAILING_MESSAGE],
        exit_mode=MethodIs,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting same as above, but with failing message
        assert res == (False, "failure_reason", None)


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
