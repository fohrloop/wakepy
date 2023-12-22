"""Tests for the wakepy.core.activation

Exception: ActivationResult is tested in it's own file
"""

import datetime as dt
import os
import re
from unittest.mock import Mock

import pytest
from freezegun import freeze_time
from testmethods import (
    METHOD_OPTIONS,
    WakepyMethodTestError,
    iterate_test_methods,
    get_test_method_class,
    METHOD_MISSING,
    FAILURE_REASON,
)

from wakepy.core import MethodUsageResult
from wakepy.core.activation import (
    StageName,
    UsageStatus,
    caniuse_fails,
    activate_using,
    get_platform_supported,
    should_fake_success,
    try_enter_and_heartbeat,
)
from wakepy.core.activationmanager import ModeActivationManager
from wakepy.core.method import Method, PlatformName, get_methods

mockmanager = Mock(spec_set=ModeActivationManager)


def test_activate_using_method_without_name():
    """Methods used for activation must have a name. If not, there should be
    a ValueError raised"""

    method = type("MyMethod", (Method,), {})()
    with pytest.raises(
        ValueError,
        match=re.escape("Methods without a name may not be used to activate modes!"),
    ):
        activate_using(method)


def test_activate_using_method_without_platform_support(monkeypatch):
    WindowsMethod = get_test_method_class(
        supported_platforms=(PlatformName.WINDOWS,),
    )

    winmethod = WindowsMethod()
    monkeypatch.setattr("wakepy.core.activation.CURRENT_PLATFORM", PlatformName.LINUX)

    # The current platform is set to linux, so method supporting only linux
    # should fail.
    res = activate_using(winmethod)
    assert res.failure_stage == StageName.PLATFORM_SUPPORT
    assert res.status == UsageStatus.FAIL


def test_activate_using_method_caniuse_fails():
    # Case 1: Fail by returning False from caniuse
    method = get_test_method_class(caniuse=False, enter_mode=True, exit_mode=True)()
    res = activate_using(method)
    assert res.status == UsageStatus.FAIL
    assert res.failure_stage == StageName.REQUIREMENTS
    assert res.message == ""

    # Case 2: Fail by returning some error reason from caniuse
    method = get_test_method_class(
        caniuse="SomeSW version <2.1.5 not supported", enter_mode=True, exit_mode=True
    )()
    res = activate_using(method)
    assert res.status == UsageStatus.FAIL
    assert res.failure_stage == StageName.REQUIREMENTS
    assert res.message == "SomeSW version <2.1.5 not supported"


def test_activate_using_method_enter_mode_fails():
    # Case: Fail by returning False from enter_mode
    method = get_test_method_class(caniuse=True, enter_mode=False)()
    res = activate_using(method)
    assert res.status == UsageStatus.FAIL
    assert res.failure_stage == StageName.ACTIVATION
    assert res.message == ""


def test_activate_using_enter_mode_success():
    method = get_test_method_class(caniuse=True, enter_mode=True)()
    res = activate_using(method)
    assert res.status == UsageStatus.SUCCESS
    assert res.failure_stage is None
    assert res.message == ""


def test_activate_using_heartbeat_success():
    method = get_test_method_class(heartbeat=True)()
    res = activate_using(method)
    assert res.status == UsageStatus.SUCCESS
    assert res.failure_stage is None
    assert res.message == ""


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
    """Tests 1) F* from TABLE 1; enter_mode failing"""

    # Case: when enter_mode returns False
    for method in iterate_test_methods(
        enter_mode=[False],
        heartbeat=METHOD_OPTIONS,
        exit_mode=METHOD_OPTIONS,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting
        # * entering to FAIL (False)
        # * empty error message (''), as returning False
        # * No heartbeat_call_time (None)
        assert res == (False, "", None)

    # Case: enter_mode returns a string (error message)
    for method in iterate_test_methods(
        enter_mode=[FAILURE_REASON],
        heartbeat=METHOD_OPTIONS,
        exit_mode=METHOD_OPTIONS,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting
        # * entering to FAIL (False)
        # * error message (FAILURE_REASON)
        # * No heartbeat_call_time (None)
        assert res == (False, FAILURE_REASON, None)


def test_try_enter_and_heartbeat_missing_missing():
    """Tests 2) MM from TABLE 1; missing both enter_mode and heartbeat"""
    for method in iterate_test_methods(
        enter_mode=[METHOD_MISSING],
        heartbeat=[METHOD_MISSING],
        exit_mode=METHOD_OPTIONS,
    ):
        # Expecting an error as missing enter_mode and heartbeat
        with pytest.raises(
            RuntimeError,
            match=re.escape(
                f"Method {method.__class__.__name__} ({method.name}) is not properly "
                "defined! Missing implementation for both, enter_mode() "
                "and heartbeat()!"
            ),
        ):
            try_enter_and_heartbeat(method)


def test_try_enter_and_heartbeat_missing_failing():
    """Tests 3) MF from TABLE 1; enter_mode missing and heartbeat failing"""
    for method in iterate_test_methods(
        enter_mode=[METHOD_MISSING],
        heartbeat=[False],
        exit_mode=METHOD_OPTIONS,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting
        # * heartbeat to FAIL (-> False)
        # * No error message (''), as returing False
        # * No heartbeat_call_time (None)
        assert res == (False, "", None)

    for method in iterate_test_methods(
        enter_mode=[METHOD_MISSING],
        heartbeat=[FAILURE_REASON],
        exit_mode=METHOD_OPTIONS,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting same as above, but with failing message
        assert res == (False, FAILURE_REASON, None)


@freeze_time("2023-12-21 16:17:00")
def test_try_enter_and_heartbeat_missing_success():
    """Tests 4) MS from TABLE 1; enter_mode missing, heartbeat success"""

    expected_time = dt.datetime.strptime(
        "2023-12-21 16:17:00", "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=dt.timezone.utc)
    for method in iterate_test_methods(
        enter_mode=[METHOD_MISSING],
        heartbeat=[True],
        exit_mode=METHOD_OPTIONS,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting: Return Success + '' +  heartbeat time
        assert res == (True, "", expected_time)


def test_try_enter_and_heartbeat_success_missing():
    """Tests 5) SM from TABLE 1; enter_mode success, heartbeat missing"""

    for method in iterate_test_methods(
        enter_mode=[True],
        heartbeat=[METHOD_MISSING],
        exit_mode=METHOD_OPTIONS,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting: Return Success + '' + None (no heartbeat)
        assert res == (True, "", None)


def test_try_enter_and_heartbeat_success_failing():
    """Tests 6) SF from TABLE 1; enter_mode success, heartbeat failing

    This should, in general Return Fail + heartbeat error message + call exit_mode()
    This call of exit_mode might be failing, so we test that separately
    """

    # Case: empty error message ("") as heartbeat returns False
    for method in iterate_test_methods(
        enter_mode=[True],
        heartbeat=[False],
        exit_mode=[True, METHOD_MISSING],
    ):
        res = try_enter_and_heartbeat(method)
        assert res == (False, "", None)

    # Case: non-empty error message (FAILURE_REASON) as heartbeat returns that
    # message
    for method in iterate_test_methods(
        enter_mode=[True],
        heartbeat=[FAILURE_REASON],
        exit_mode=[True, METHOD_MISSING],
    ):
        res = try_enter_and_heartbeat(method)
        assert res == (False, FAILURE_REASON, None)

    # Case: The heartbeat fails, and because enter_mode() has succeed, wakepy
    # tries to call exit_mode(). If that fails, the program must crash, as we
    # are in an unknown state and this is clearly an error.
    for method in iterate_test_methods(
        enter_mode=[True],
        heartbeat=[False, FAILURE_REASON],
        exit_mode=[False, FAILURE_REASON],
    ):
        with pytest.raises(
            RuntimeError,
            match=re.escape(
                f"Entered {method.__class__.__name__} ({method.name}) but could not "
                "exit!"
            ),
        ):
            try_enter_and_heartbeat(method)

    # Case: Same as the one above, but this time exit_mode() raises a
    # WakepyMethodTestError. That is raised (and not catched), instead.
    # If this happens, the Method.exit_mode() has a bug.
    for method in iterate_test_methods(
        enter_mode=[True],
        heartbeat=[False, FAILURE_REASON],
        exit_mode=[WakepyMethodTestError("foo")],
    ):
        with pytest.raises(
            WakepyMethodTestError,
            match="foo",
        ):
            try_enter_and_heartbeat(method)


@freeze_time("2023-12-21 16:17:00")
def test_try_enter_and_heartbeat_success_success():
    """Tests 7) SS from TABLE 1; enter_mode success & heartbeat success"""
    expected_time = dt.datetime.strptime(
        "2023-12-21 16:17:00", "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=dt.timezone.utc)

    for method in iterate_test_methods(
        enter_mode=[True],
        heartbeat=[True],
        exit_mode=METHOD_OPTIONS,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting Return Success + '' + heartbeat time
        assert res == (True, "", expected_time)


def test_try_enter_and_heartbeat_special_cases():
    # Case: returning bad value (only bool and str accepted)
    for method_name in ("enter_mode", "heartbeat"):
        method = get_test_method_class(**{method_name: 132})()
        with pytest.raises(
            RuntimeError,
            match=re.escape(
                f"The {method_name} of {method.__class__.__name__} ({method.name}) returned a "
                "value of unsupported type. The supported types are: bool, str. "
                "Returned value: 132"
            ),
        ):
            try_enter_and_heartbeat(method)


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


@pytest.mark.parametrize(
    "status, failure_stage, method_name, message, expected_string_representation",
    [
        (
            UsageStatus.FAIL,
            StageName.PLATFORM_SUPPORT,
            "fail-platform",
            "Platform XYZ not supported!",
            '(FAIL @PLATFORM_SUPPORT, fail-platform, "Platform XYZ not supported!")',
        ),
        (
            UsageStatus.FAIL,
            StageName.REQUIREMENTS,
            "other-fail-method",
            "Need SW X version >= 8.9!",
            '(FAIL @REQUIREMENTS, other-fail-method, "Need SW X version >= 8.9!")',
        ),
        (
            UsageStatus.SUCCESS,
            None,
            "successfulMethod",
            "",
            # Succesful methods do not print empty message
            "(SUCCESS, successfulMethod)",
        ),
        (
            UsageStatus.UNUSED,
            None,
            "SomeMethod",
            "",
            # Unused methods do not print empty message
            "(UNUSED, SomeMethod)",
        ),
    ],
)
def test_method_usage_result(
    status,
    failure_stage,
    method_name,
    message,
    expected_string_representation,
):
    mur = MethodUsageResult(
        status=status,
        failure_stage=failure_stage,
        method_name=method_name,
        message=message,
    )
    # These attributes are available
    assert mur.status == status
    assert mur.failure_stage == failure_stage
    assert mur.method_name == method_name
    assert mur.message == message

    assert str(mur) == expected_string_representation


def test_stagename():
    assert StageName.PLATFORM_SUPPORT == "PLATFORM_SUPPORT"
    assert StageName.ACTIVATION == "ACTIVATION"
    assert StageName.REQUIREMENTS == "REQUIREMENTS"


def test_usagestatus():
    assert UsageStatus.FAIL == "FAIL"
    assert UsageStatus.SUCCESS == "SUCCESS"
    assert UsageStatus.UNUSED == "UNUSED"


def test_should_fake_success(monkeypatch):
    # These are the only "falsy" values for WAKEPY_FAKE_SUCCESS
    for val in ("0", "no", "NO", "False", "false", "FALSE"):
        with monkeypatch.context() as mp:
            mp.setenv("WAKEPY_FAKE_SUCCESS", val)
            val_from_env = os.environ.get("WAKEPY_FAKE_SUCCESS")
            assert val_from_env == str(val)
            assert should_fake_success() is False
    # Anything else is considered truthy
    for val in ("1", "yes", "True", "anystring"):
        with monkeypatch.context() as mp:
            mp.setenv("WAKEPY_FAKE_SUCCESS", val)
            val_from_env = os.environ.get("WAKEPY_FAKE_SUCCESS")
            assert val_from_env == str(val)
            assert should_fake_success() is True
