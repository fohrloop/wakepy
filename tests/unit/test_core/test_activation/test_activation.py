"""Tests for the wakepy.core.activation

Exception: ActivationResult is tested in it's own file
"""

import datetime as dt
import os
import re
from unittest.mock import Mock

import pytest
import time_machine
from testmethods import (
    FAILURE_REASON,
    METHOD_MISSING,
    METHOD_OPTIONS,
    WakepyMethodTestError,
    get_test_method_class,
    iterate_test_methods,
)

from wakepy.core import MethodActivationResult
from wakepy.core.activation import (
    StageName,
    WakepyFakeSuccess,
    activate_method,
    activate_one_of_multiple,
    caniuse_fails,
    deactivate_method,
    get_platform_supported,
    try_enter_and_heartbeat,
)
from wakepy.core.calls import CallProcessor
from wakepy.core.heartbeat import Heartbeat
from wakepy.core.method import Method, MethodError, PlatformName, get_methods


def test_activate_without_methods(monkeypatch):
    _arrange_for_test_activate(monkeypatch)
    res, active_method, heartbeat = activate_one_of_multiple([], None)
    assert res.list_methods() == []
    assert res.success is False
    assert active_method is None
    assert heartbeat is None


def test_activate_function_success(monkeypatch):
    """Here we test the activate_one_of_multiple() function. It calls some
    other functions which we do not care about as they're tested elsewhere.
    That is we why monkeypatch those functions with fakes"""

    # Arrange
    mocks = _arrange_for_test_activate(monkeypatch)
    methodcls_fail = get_test_method_class(enter_mode=False)
    methodcls_success = get_test_method_class(enter_mode=True)

    # Act
    # Note: prioritize the failing first, so that the failing one will also be
    # used. This also tests at that the prioritization is used at least
    # somehow
    result, active_method, heartbeat = activate_one_of_multiple(
        [methodcls_success, methodcls_fail],
        call_processor=mocks.call_processor,
        methods_priority=[
            methodcls_fail.name,
            methodcls_success.name,
        ],
    )

    # Assert

    # There is a successful method, so the activation succeeds.
    assert result.success is True

    # The failing method is tried first because there is prioritization step
    # which honors the `methods_priority``
    assert [x.method_name for x in result.list_methods()] == [
        methodcls_fail.name,
        methodcls_success.name,
    ]

    assert isinstance(active_method, methodcls_success)
    assert heartbeat is mocks.heartbeat


def test_activate_function_failure(monkeypatch):
    # Arrange
    mocks = _arrange_for_test_activate(monkeypatch)
    methodcls_fail = get_test_method_class(enter_mode=False)

    # Act
    result, active_method, heartbeat = activate_one_of_multiple(
        [methodcls_fail],
        call_processor=mocks.call_processor,
    )

    # Assert
    # The activation failed, so active_method and heartbeat is None
    assert result.success is False
    assert active_method is None
    assert heartbeat is None


def _arrange_for_test_activate(monkeypatch):
    """This is the test arrangement step for tests for the
    `activate_one_of_multiple` function"""

    mocks = Mock()
    mocks.heartbeat = Mock(spec_set=Heartbeat)
    mocks.call_processor = Mock(spec_set=CallProcessor)

    def fake_activate_method(method):
        success = method.enter_mode()
        return (
            MethodActivationResult(
                method_name=method.name,
                success=True if success else False,
                failure_stage=None if success else StageName.ACTIVATION,
            ),
            mocks.heartbeat,
        )

    monkeypatch.setattr("wakepy.core.activation.activate_method", fake_activate_method)
    monkeypatch.setattr(
        "wakepy.core.activation.check_methods_priority", mocks.check_methods_priority
    )
    monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "0")
    return mocks


def test_activate_method_method_without_name():
    """Methods used for activation must have a name. If not, there should be
    a ValueError raised"""

    method = type("MyMethod", (Method,), {})()
    with pytest.raises(
        ValueError,
        match=re.escape("Methods without a name may not be used to activate modes!"),
    ):
        activate_method(method)


def test_activate_method_method_without_platform_support(monkeypatch):
    WindowsMethod = get_test_method_class(
        supported_platforms=(PlatformName.WINDOWS,),
    )

    winmethod = WindowsMethod()
    monkeypatch.setattr("wakepy.core.activation.CURRENT_PLATFORM", PlatformName.LINUX)

    # The current platform is set to linux, so method supporting only linux
    # should fail.
    res, heartbeat = activate_method(winmethod)
    assert res.failure_stage == StageName.PLATFORM_SUPPORT
    assert res.success is False
    assert heartbeat is None


def test_activate_method_method_caniuse_fails():
    # Case 1: Fail by returning False from caniuse
    method = get_test_method_class(caniuse=False, enter_mode=True, exit_mode=True)()
    res, heartbeat = activate_method(method)
    assert res.success is False
    assert res.failure_stage == StageName.REQUIREMENTS
    assert res.failure_reason == ""
    assert heartbeat is None

    # Case 2: Fail by returning some error reason from caniuse
    method = get_test_method_class(
        caniuse="SomeSW version <2.1.5 not supported", enter_mode=True, exit_mode=True
    )()
    res, heartbeat = activate_method(method)
    assert res.success is False
    assert res.failure_stage == StageName.REQUIREMENTS
    assert res.failure_reason == "SomeSW version <2.1.5 not supported"
    assert heartbeat is None


def test_activate_method_method_enter_mode_fails():
    # Case: Fail by returning False from enter_mode
    method = get_test_method_class(caniuse=True, enter_mode=RuntimeError("failed"))()
    res, heartbeat = activate_method(method)
    assert res.success is False
    assert res.failure_stage == StageName.ACTIVATION
    assert "Original error: failed" in res.failure_reason
    assert heartbeat is None


def test_activate_method_enter_mode_success():
    method = get_test_method_class(caniuse=True, enter_mode=None)()
    res, heartbeat = activate_method(method)
    assert res.success is True
    assert res.failure_stage is None
    assert res.failure_reason == ""
    # No heartbeat on success, as the used Method does not have heartbeat()
    assert heartbeat is None


def test_activate_method_heartbeat_success():
    method = get_test_method_class(heartbeat=None)()
    res, heartbeat = activate_method(method)
    assert res.success is True
    assert res.failure_stage is None
    assert res.failure_reason == ""
    # We get a Heartbeat instance on success, as the used Method does has a
    # heartbeat()
    assert isinstance(heartbeat, Heartbeat)


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

    # Case: enter_mode raises exception
    for method in iterate_test_methods(
        enter_mode=[RuntimeError(FAILURE_REASON)],
        heartbeat=METHOD_OPTIONS,
        exit_mode=METHOD_OPTIONS,
    ):
        success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)
        # Expecting
        # * entering to FAIL
        # * error message (FAILURE_REASON)
        # * No heartbeat_call_time (None)
        assert success is False
        assert FAILURE_REASON in err_message
        assert heartbeat_call_time is None


def test_try_enter_and_heartbeat_missing_missing():
    """Tests 2) MM from TABLE 1; missing both enter_mode and heartbeat"""
    for method in iterate_test_methods(
        enter_mode=[METHOD_MISSING],
        heartbeat=[METHOD_MISSING],
        exit_mode=METHOD_OPTIONS,
    ):
        expected_errmsg = (
            f"Method {method.__class__.__name__} ({method.name}) is not properly "
            "defined! Missing implementation for both, enter_mode() "
            "and heartbeat()!"
        )

        success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)

        # Expecting an error as missing enter_mode and heartbeat
        assert success is False
        assert err_message == expected_errmsg
        assert heartbeat_call_time is None


def test_try_enter_and_heartbeat_missing_failing():
    """Tests 3) MF from TABLE 1; enter_mode missing and heartbeat failing"""
    for method in iterate_test_methods(
        enter_mode=[METHOD_MISSING],
        heartbeat=[False],
        exit_mode=METHOD_OPTIONS,
    ):
        success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)
        # Expecting
        # * heartbeat to FAIL (-> success is False)
        # * Error message saying that can only return None
        # * No heartbeat_call_time (None)
        assert success is False
        assert "returned an unsupported value False." in err_message
        assert "The only accepted return value is None" in err_message
        assert heartbeat_call_time is None

    for method in iterate_test_methods(
        enter_mode=[METHOD_MISSING],
        heartbeat=[FAILURE_REASON],
        exit_mode=METHOD_OPTIONS,
    ):
        success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)
        # Expecting same as above, but with failing message
        assert success is False
        assert f"returned an unsupported value {FAILURE_REASON}." in err_message
        assert "The only accepted return value is None" in err_message
        assert heartbeat_call_time is None


@time_machine.travel(
    dt.datetime(2023, 12, 21, 16, 17, tzinfo=dt.timezone.utc), tick=False
)
def test_try_enter_and_heartbeat_missing_success():
    """Tests 4) MS from TABLE 1; enter_mode missing, heartbeat success"""

    expected_time = dt.datetime.strptime(
        "2023-12-21 16:17:00", "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=dt.timezone.utc)
    for method in iterate_test_methods(
        enter_mode=[METHOD_MISSING],
        heartbeat=[None],
        exit_mode=METHOD_OPTIONS,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting: Return Success + '' +  heartbeat time
        assert res == (True, "", expected_time)


def test_try_enter_and_heartbeat_success_missing():
    """Tests 5) SM from TABLE 1; enter_mode success, heartbeat missing"""

    for method in iterate_test_methods(
        enter_mode=[None],
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

    # Case: Heartbeate fails by raising RuntimeError
    for method in iterate_test_methods(
        enter_mode=[None],
        heartbeat=[RuntimeError(FAILURE_REASON)],
        exit_mode=[None, METHOD_MISSING],
    ):
        success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)
        assert success is False
        assert f"Original error: {FAILURE_REASON}" in err_message
        assert heartbeat_call_time is None

    # Case: The heartbeat fails, and because enter_mode() has succeed, wakepy
    # tries to call exit_mode(). If that fails, the program must crash, as we
    # are in an unknown state and this is clearly an error.
    for method in iterate_test_methods(
        enter_mode=[None],
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
    # WakepyMethodTestError. That is re-raised as RuntimeError, instead.
    # If this happens, the Method.exit_mode() has a bug.
    for method in iterate_test_methods(
        enter_mode=[None],
        heartbeat=[False, FAILURE_REASON],
        exit_mode=[WakepyMethodTestError("foo")],
    ):
        with pytest.raises(
            RuntimeError,
            match="foo",
        ):
            try_enter_and_heartbeat(method)


@time_machine.travel(
    dt.datetime(2023, 12, 21, 16, 17, tzinfo=dt.timezone.utc), tick=False
)
def test_try_enter_and_heartbeat_success_success():
    """Tests 7) SS from TABLE 1; enter_mode success & heartbeat success"""
    expected_time = dt.datetime.strptime(
        "2023-12-21 16:17:00", "%Y-%m-%d %H:%M:%S"
    ).replace(tzinfo=dt.timezone.utc)

    for method in iterate_test_methods(
        enter_mode=[None],
        heartbeat=[None],
        exit_mode=METHOD_OPTIONS,
    ):
        res = try_enter_and_heartbeat(method)
        # Expecting Return Success + '' + heartbeat time
        assert res == (True, "", expected_time)


def test_try_enter_and_heartbeat_special_cases():
    # Case: returning bad value (only bool and str accepted)
    for method_name in ("enter_mode", "heartbeat"):
        method = get_test_method_class(**{method_name: 132})()
        success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)

        assert success is False
        assert "The only accepted return value is None" in err_message
        assert heartbeat_call_time is None


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
    "success, failure_stage, method_name, message, expected_string_representation",
    [
        (
            False,
            StageName.PLATFORM_SUPPORT,
            "fail-platform",
            "Platform XYZ not supported!",
            '(FAIL @PLATFORM_SUPPORT, fail-platform, "Platform XYZ not supported!")',
        ),
        (
            False,
            StageName.REQUIREMENTS,
            "other-fail-method",
            "Need SW X version >= 8.9!",
            '(FAIL @REQUIREMENTS, other-fail-method, "Need SW X version >= 8.9!")',
        ),
        (
            True,
            None,
            "successfulMethod",
            "",
            # Succesful methods do not print empty message
            "(SUCCESS, successfulMethod)",
        ),
        (
            None,
            None,
            "SomeMethod",
            "",
            # Unused methods do not print empty message
            "(UNUSED, SomeMethod)",
        ),
    ],
)
def test_method_usage_result(
    success,
    failure_stage,
    method_name,
    message,
    expected_string_representation,
):
    mur = MethodActivationResult(
        success=success,
        failure_stage=failure_stage,
        method_name=method_name,
        failure_reason=message,
    )
    # These attributes are available
    assert mur.method_name == method_name
    assert mur.success == success
    assert mur.failure_stage == failure_stage
    assert mur.failure_reason == message

    assert str(mur) == expected_string_representation


def test_deactivate_success_no_heartbeat():
    method = get_test_method_class(enter_mode=None, exit_mode=None)()
    deactivate_method(method)


def test_deactivate_success_with_heartbeat():
    heartbeat = Mock(spec_set=Heartbeat)
    heartbeat.stop.return_value = True
    method = get_test_method_class(enter_mode=None, exit_mode=None)()
    deactivate_method(method, heartbeat=heartbeat)


def test_deactivate_success_with_heartbeat_and_no_exit():
    heartbeat = Mock(spec_set=Heartbeat)
    heartbeat.stop.return_value = True
    method = get_test_method_class(enter_mode=None)()
    deactivate_method(method, heartbeat=heartbeat)


def test_deactivate_fail_exit_mode_returning_bad_value():
    method = get_test_method_class(enter_mode=None, exit_mode=123)()
    with pytest.raises(
        MethodError,
        match=re.escape(
            f"The exit_mode of '{method.__class__.__name__}' ({method.name}) was "
            "unsuccessful!"
        )
        + " .* "
        + re.escape("Original error: exit_mode returned a value other than None!"),
    ):
        deactivate_method(method)


def test_deactivate_failing_exit_mode():
    method = get_test_method_class(enter_mode=None, exit_mode=Exception("oh no"))()
    with pytest.raises(
        MethodError,
        match=re.escape(
            f"The exit_mode of '{method.__class__.__name__}' ({method.name}) was "
            "unsuccessful"
        )
        + ".*"
        + re.escape("Original error: oh no"),
    ):
        deactivate_method(method)


def test_deactivate_fail_heartbeat_not_stopping():
    heartbeat = Mock(spec_set=Heartbeat)
    heartbeat.stop.return_value = "Bad value"
    method = get_test_method_class(enter_mode=None, exit_mode=None)()
    with pytest.raises(
        MethodError,
        match=re.escape(
            f"The heartbeat of {method.__class__.__name__} ({method.name}) could not "
            "be stopped! Suggesting submitting a bug report and rebooting for clearing "
            "the mode."
        ),
    ):
        deactivate_method(method, heartbeat)


def test_stagename():
    assert StageName.PLATFORM_SUPPORT == "PLATFORM_SUPPORT"
    assert StageName.ACTIVATION == "ACTIVATION"
    assert StageName.REQUIREMENTS == "REQUIREMENTS"


def test_wakepy_fake_success(monkeypatch):
    method = WakepyFakeSuccess()

    # These are the only "falsy" values for WAKEPY_FAKE_SUCCESS
    for val in ("0", "no", "NO", "False", "false", "FALSE"):
        with monkeypatch.context() as mp:
            mp.setenv("WAKEPY_FAKE_SUCCESS", val)
            val_from_env = os.environ.get("WAKEPY_FAKE_SUCCESS")
            assert val_from_env == str(val)
            assert method.enter_mode() is False
    # Anything else is considered truthy
    for val in ("1", "yes", "True", "anystring"):
        with monkeypatch.context() as mp:
            mp.setenv("WAKEPY_FAKE_SUCCESS", val)
            val_from_env = os.environ.get("WAKEPY_FAKE_SUCCESS")
            assert val_from_env == str(val)
            assert method.enter_mode() is True

    if "WAKEPY_FAKE_SUCCESS" in os.environ:
        monkeypatch.delenv("WAKEPY_FAKE_SUCCESS")
    assert method.enter_mode() is False
