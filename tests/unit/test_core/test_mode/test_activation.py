"""Tests for the wakepy.core.activation

Exception: ActivationResult is tested in it's own file
"""

import datetime as dt
import os
import re
from contextlib import contextmanager
from unittest.mock import Mock

import pytest
import time_machine

from tests.unit.test_core.testmethods import (
    FAILURE_REASON,
    METHOD_MISSING,
    METHOD_OPTIONS,
    WakepyMethodTestError,
    get_test_method_class,
    iterate_test_methods,
)
from wakepy.core import (
    DBusAdapter,
    Method,
    MethodActivationResult,
    PlatformName,
    get_methods,
)
from wakepy.core.constants import WAKEPY_FAKE_SUCCESS, StageName, StageNameValue
from wakepy.core.heartbeat import Heartbeat
from wakepy.core.method import MethodError
from wakepy.core.mode import (
    activate_method,
    activate_mode,
    caniuse_fails,
    deactivate_method,
    get_platform_supported,
    try_enter_and_heartbeat,
)
from wakepy.core.registry import get_method


@pytest.fixture
def heartbeat1():
    """Well behaving Heartbeat instance"""
    heartbeat = Mock(spec_set=Heartbeat)
    heartbeat.stop.return_value = True
    return heartbeat


@pytest.fixture
def heartbeat2_bad():
    """Bad Heartbeat instance. Returns a bad value."""
    heartbeat = Mock(spec_set=Heartbeat)
    heartbeat.stop.return_value = "Bad value"
    return heartbeat


class TestActivateMode:
    """tests for activate_mode"""

    @pytest.mark.usefixtures("mocks_for_test_activate_mode")
    def test_activate_without_methods(self):
        res, active_method, heartbeat = activate_mode([], None)
        assert res.list_methods() == []
        assert res.success is False
        assert active_method is None
        assert heartbeat is None

    def test_activate_function_success(self, mocks_for_test_activate_mode):
        """Here we test the activate_mode() function. It calls some
        other functions which we do not care about as they're tested elsewhere.
        That is we why monkeypatch those functions with fakes"""

        # Arrange
        mocks = mocks_for_test_activate_mode
        methodcls_fail = get_test_method_class(enter_mode=False)
        methodcls_success = get_test_method_class(enter_mode=None)

        # Act
        # Note: prioritize the failing first, so that the failing one will also
        # be used. This also tests at that the prioritization is used at least
        # somehow
        result, active_method, heartbeat = activate_mode(
            [methodcls_success, methodcls_fail],
            dbus_adapter=mocks.dbus_adapter,
            methods_priority=[
                methodcls_fail.name,
                methodcls_success.name,
            ],
        )

        # Assert

        # There is a successful method, so the activation succeeds.
        assert result.success is True

        # The failing method is tried first because there is prioritization
        # step which honors the `methods_priority`
        assert [x.method_name for x in result.list_methods()] == [
            methodcls_fail.name,
            methodcls_success.name,
        ]

        assert isinstance(active_method, methodcls_success)
        assert heartbeat is mocks.heartbeat

    def test_activate_function_failure(self, mocks_for_test_activate_mode):
        # Arrange
        mocks = mocks_for_test_activate_mode
        methodcls_fail = get_test_method_class(enter_mode=False)

        # Act
        result, active_method, heartbeat = activate_mode(
            [methodcls_fail],
            dbus_adapter=mocks.dbus_adapter,
        )

        # Assert
        # The activation failed, so active_method and heartbeat is None
        assert result.success is False
        assert active_method is None
        assert heartbeat is None

    @staticmethod
    @pytest.fixture
    def mocks_for_test_activate_mode(monkeypatch, heartbeat1):
        """This is the test arrangement step for tests for the
        `activate_mode` function"""

        mocks = Mock()
        mocks.heartbeat = heartbeat1
        mocks.dbus_adapter = Mock(spec_set=DBusAdapter)

        def fake_activate_method(method):
            try:
                assert method.enter_mode() is None
                success = True
            except Exception:
                success = False

            return (
                MethodActivationResult(
                    method_name=method.name,
                    success=True if success else False,
                    failure_stage=None if success else StageName.ACTIVATION,
                ),
                mocks.heartbeat,
            )

        monkeypatch.setattr("wakepy.core.mode.activate_method", fake_activate_method)
        monkeypatch.setattr(
            "wakepy.core.mode.check_methods_priority",
            mocks.check_methods_priority,
        )
        monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "0")
        return mocks


class TestActivateMethod:
    """tests for activate_method"""

    def test_activate_method_method_without_name(self):
        """Methods used for activation must have a name. If not, there should
        be a ValueError raised"""

        method = type("MyMethod", (Method,), {})()
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Methods without a name may not be used to activate modes!"
            ),
        ):
            activate_method(method)

    def test_activate_method_method_without_platform_support(self, monkeypatch):
        WindowsMethod = get_test_method_class(
            supported_platforms=(PlatformName.WINDOWS,),
        )

        winmethod = WindowsMethod()
        monkeypatch.setattr("wakepy.core.mode.CURRENT_PLATFORM", PlatformName.LINUX)

        # The current platform is set to linux, so method supporting only linux
        # should fail.
        res, heartbeat = activate_method(winmethod)
        assert res.failure_stage == StageName.PLATFORM_SUPPORT
        assert res.success is False
        assert heartbeat is None

    def test_activate_method_method_caniuse_fails(self):
        # Case 1: Fail by returning False from caniuse
        method = get_test_method_class(caniuse=False, enter_mode=True, exit_mode=True)()
        res, heartbeat = activate_method(method)
        assert res.success is False
        assert res.failure_stage == StageName.REQUIREMENTS
        assert res.failure_reason == ""
        assert heartbeat is None

        # Case 2: Fail by returning some error reason from caniuse
        method = get_test_method_class(
            caniuse="SomeSW version <2.1.5 not supported",
            enter_mode=True,
            exit_mode=True,
        )()
        res, heartbeat = activate_method(method)
        assert res.success is False
        assert res.failure_stage == StageName.REQUIREMENTS
        assert res.failure_reason == "SomeSW version <2.1.5 not supported"
        assert heartbeat is None

    def test_activate_method_method_enter_mode_fails(self):
        # Case: Fail by returning False from enter_mode
        method = get_test_method_class(
            caniuse=True, enter_mode=RuntimeError("failed")
        )()
        res, heartbeat = activate_method(method)
        assert res.success is False
        assert res.failure_stage == StageName.ACTIVATION
        assert "RuntimeError('failed')" in res.failure_reason
        assert heartbeat is None

    def test_activate_method_enter_mode_success(self):
        method = get_test_method_class(caniuse=True, enter_mode=None)()
        res, heartbeat = activate_method(method)
        assert res.success is True
        assert res.failure_stage is None
        assert res.failure_reason == ""
        # No heartbeat on success, as the used Method does not have heartbeat()
        assert heartbeat is None

    def test_activate_method_heartbeat_success(self):
        method = get_test_method_class(heartbeat=None)()
        res, heartbeat = activate_method(method)
        assert res.success is True
        assert res.failure_stage is None
        assert res.failure_reason == ""
        # We get a Heartbeat instance on success, as the used Method does has a
        # heartbeat()
        assert isinstance(heartbeat, Heartbeat)


class TestTryEnterAndHeartbeat:
    """tests for try_enter_and_heartbeat

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

    def test_enter_mode_failing(self):
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

    def test_enter_mode_missing_and_heartbeat(self):
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

    def test_enter_mode_missing_heartbeat_failing(self):
        """Tests 3) MF from TABLE 1; enter_mode missing and heartbeat
        failing"""
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
    def test_enter_mode_missing_heartbeat_success(self):
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

    def test_enter_mode_success_hearbeat_missing(self):
        """Tests 5) SM from TABLE 1; enter_mode success, heartbeat missing"""

        for method in iterate_test_methods(
            enter_mode=[None],
            heartbeat=[METHOD_MISSING],
            exit_mode=METHOD_OPTIONS,
        ):
            res = try_enter_and_heartbeat(method)
            # Expecting: Return Success + '' + None (no heartbeat)
            assert res == (True, "", None)

    def test_enter_mode_success_heartbeat_failing(self):
        """Tests 6) SF from TABLE 1; enter_mode success, heartbeat failing

        This should, in general Return Fail + heartbeat error message + call
        exit_mode() This call of exit_mode might be failing, so we test that
        separately
        """

        # Case: Heartbeate fails by raising RuntimeError
        for method in iterate_test_methods(
            enter_mode=[None],
            heartbeat=[RuntimeError(FAILURE_REASON)],
            exit_mode=[None, METHOD_MISSING],
        ):
            success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)
            assert success is False
            assert f"{FAILURE_REASON}" in err_message
            assert heartbeat_call_time is None

        # Case: The heartbeat fails, and because enter_mode() has succeed,
        # wakepy tries to call exit_mode(). If that fails, the program must
        # crash, as we are in an unknown state and this is clearly an error.
        for method in iterate_test_methods(
            enter_mode=[None],
            heartbeat=[False, FAILURE_REASON],
            exit_mode=[False, FAILURE_REASON],
        ):
            with pytest.raises(
                RuntimeError,
                match=re.escape(
                    f"Entered {method.__class__.__name__} ({method.name}) but could not"
                    " exit!"
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
    def test_enter_mode_success_heartbeat_success(self):
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

    def test_enter_mode_returns_bad_balue(self):
        # Case: returning bad value (None return value accepted)
        method = get_test_method_class(**{"enter_mode": 132})()
        success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)

        assert success is False
        assert "The only accepted return value is None" in err_message
        assert heartbeat_call_time is None

    def test_heartbeat_returns_bad_balue(self):
        # Case: returning bad value (None return value accepted)
        method = get_test_method_class(**{"heartbeat": 132})()
        success, err_message, heartbeat_call_time = try_enter_and_heartbeat(method)

        assert success is False
        assert "The only accepted return value is None" in err_message
        assert heartbeat_call_time is None


class TestPlatformSupported:
    """tests for get_platform_supported"""

    @pytest.mark.usefixtures("provide_methods_different_platforms")
    def test_get_platform_supported(self):
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


class TestCanIUseFails:
    """test caniuse_fails"""

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
            # If .caniuse() returns anything else than a string, that is
            # silently converted to a string, and the check fails.
            dict(caniuse=123, expected=(True, "123")),
        ],
    )
    def test_normal_cases(self, params):
        class SomeMethod(Method):
            def caniuse(self):
                return params["caniuse"]

        assert caniuse_fails(SomeMethod()) == params["expected"]

    def test_special_case(self):
        """Tests the case when Method.caniuse raises an exception"""
        err = ValueError("Cannot use")

        class SomeMethod(Method):
            def caniuse(self):
                raise err

        method = SomeMethod()
        assert caniuse_fails(method) == (True, str(err))


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
def test_method_activation_result(
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


class TestDeactivateMethod:

    def test_success_no_heartbeat(self):
        method = get_test_method_class(enter_mode=None, exit_mode=None)()
        deactivate_method(method)

    def test_success_with_heartbeat(self, heartbeat1):
        method = get_test_method_class(
            enter_mode=None, heartbeat=None, exit_mode=None
        )()
        deactivate_method(method, heartbeat=heartbeat1)

    def test_success_with_heartbeat_and_no_exit(self, heartbeat1):
        method = get_test_method_class(enter_mode=None, heartbeat=None)()
        deactivate_method(method, heartbeat=heartbeat1)

    def test_fail_deactivation_at_exit_mode_bad_value(self):
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

    def test_fail_deactivation_at_exit_mode_raises_exception(self):
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

    def test_fail_deactivation_heartbeat_not_stopping(self, heartbeat2_bad):

        method = get_test_method_class(enter_mode=None, exit_mode=None)()
        with pytest.raises(
            MethodError,
            match=re.escape(
                f"The heartbeat of {method.__class__.__name__} ({method.name}) could "
                "not be stopped! Suggesting submitting a bug report and rebooting for "
                "clearing the mode."
            ),
        ):
            deactivate_method(method, heartbeat2_bad)


def test_stagename(assert_strenum_values):
    assert StageName.PLATFORM_SUPPORT == "PLATFORM_SUPPORT"
    assert StageName.ACTIVATION == "ACTIVATION"
    assert StageName.REQUIREMENTS == "REQUIREMENTS"
    assert_strenum_values(StageName, StageNameValue)


class TestWakepyFakeSuccess:

    wakepy_fake_success_cls = get_method(WAKEPY_FAKE_SUCCESS)

    @contextmanager
    def wakepy_fake_value_set(self, monkeypatch, val):
        with monkeypatch.context() as mp:
            mp.setenv("WAKEPY_FAKE_SUCCESS", val)
            val_from_env = os.environ.get("WAKEPY_FAKE_SUCCESS")
            assert val_from_env == str(val)
            yield

    # These are the only "falsy" values for WAKEPY_FAKE_SUCCESS
    @pytest.mark.parametrize("val", ("0", "no", "NO", "False", "false", "FALSE"))
    def test_falsy_values(self, val, monkeypatch):
        method = self.wakepy_fake_success_cls()

        with self.wakepy_fake_value_set(monkeypatch, val), pytest.raises(
            RuntimeError, match=f"WAKEPY_FAKE_SUCCESS set to falsy value: {val}"
        ):
            method.enter_mode()

    @pytest.mark.parametrize("val", ("1", "yes", "True", "anystring"))
    def test_truthy_values(self, val, monkeypatch):
        method = self.wakepy_fake_success_cls()

        with self.wakepy_fake_value_set(monkeypatch, val):
            assert method.enter_mode() is None  # type: ignore[func-returns-value]

    def test_without_the_env_var_set(self, monkeypatch):
        method = self.wakepy_fake_success_cls()
        if "WAKEPY_FAKE_SUCCESS" in os.environ:
            monkeypatch.delenv("WAKEPY_FAKE_SUCCESS")

        with pytest.raises(RuntimeError, match="WAKEPY_FAKE_SUCCESS not set"):
            method.enter_mode()
