from __future__ import annotations

import copy
import os
import re
import typing
import warnings
from contextlib import contextmanager
from unittest.mock import Mock

import pytest

from tests.unit.test_core.testmethods import get_test_method_class
from wakepy import ActivationError, ActivationResult, Method, Mode
from wakepy.core.activationresult import MethodActivationResult
from wakepy.core.constants import WAKEPY_FAKE_SUCCESS, StageName
from wakepy.core.dbus import DBusAdapter
from wakepy.core.mode import (
    ModeExit,
    activate_mode,
    add_fake_success_if_required,
    handle_activation_fail,
    select_methods,
    should_fake_success,
)
from wakepy.core.registry import get_method, get_methods

if typing.TYPE_CHECKING:
    from typing import List, Type


@pytest.fixture
def dbus_adapter_cls():
    class TestDbusAdapter(DBusAdapter): ...

    return TestDbusAdapter


@pytest.fixture
def testmode_cls():
    class TestMode(Mode): ...

    return TestMode


@pytest.fixture
def methods_abc(monkeypatch, testutils) -> List[Type[Method]]:
    """This fixture creates three methods, which belong to a given mode."""
    testutils.empty_method_registry(monkeypatch, fake_success=True)

    class MethodA(Method):
        name = "MethodA"
        mode = "foo"

    class MethodB(Method):
        name = "MethodB"
        mode = "foo"

    class MethodC(Method):
        name = "MethodC"
        mode = "foo"

    return [MethodA, MethodB, MethodC]


@pytest.fixture
def methods_priority0():
    return ["*"]


@pytest.fixture
def mode0(
    methods_abc: List[Type[Method]],
    testmode_cls: Type[Mode],
    methods_priority0: List[str],
):
    return testmode_cls(
        methods_abc,
        dbus_adapter=None,
        methods_priority=methods_priority0,
        name="TestMode",
    )


@pytest.fixture
def mode1_with_dbus(
    methods_abc: List[Type[Method]],
    testmode_cls: Type[Mode],
    methods_priority0: List[str],
    dbus_adapter_cls: Type[DBusAdapter],
):
    return testmode_cls(
        methods_abc,
        methods_priority=methods_priority0,
        dbus_adapter=dbus_adapter_cls,
        name="TestMode1",
    )


def test_mode_contextmanager_protocol(
    mode0: Mode,
):
    """Test that the Mode fulfills the context manager protocol"""
    flag_end_of_with_block = False

    # Test that the context manager protocol works
    with mode0 as m:

        # The __enter__ returns the Mode
        assert m is mode0
        # We have activated the Mode
        assert mode0.active
        # There is an ActivationResult available in .activation_result
        assert isinstance(m.activation_result, ActivationResult)
        # The active method is also available
        assert isinstance(mode0.active_method, Method)

        activation_result = copy.deepcopy(m.activation_result)
        flag_end_of_with_block = True

    # reached the end of the with block
    assert flag_end_of_with_block

    # After exiting the mode, Mode.active is set to False
    assert m.active is False
    # The active_method is set to None
    assert m.active_method is None
    # The activation result is still there (not removed during deactivation)
    assert activation_result == m.activation_result


class TestModeActivateDeactivate:
    """Tests for Mode._activate and Mode._deactivate"""

    def test_activate_twice(
        self,
        mode1_with_dbus: Mode,
    ):
        # Run twice. The dbus adapter instance is created on the first time
        # and reused the second time.
        with mode1_with_dbus:
            ...
        with mode1_with_dbus:
            ...

    def test_runtime_error_if_deactivating_without_active_mode(
        self,
        mode0: Mode,
    ):
        # Try to deactivate a mode when there's no active_method. Needed for
        # test coverage. A situation like this is unlikely to happen ever.
        with pytest.raises(
            RuntimeError,
            match="Cannot deactivate mode: TestMode. The active_method is None! This should never happen",  # noqa: E501
        ):
            with mode0:
                # Setting active method
                mode0.active_method = None


class TestExitModeWithException:
    """Test cases when a Mode is exited with an Exception"""

    def test_mode_exits_with_modeexit(self, mode0: Mode):
        with mode0:
            testval = 2
            raise ModeExit
            testval = 0  # type: ignore # (never hit)

        assert testval == 2

    def test_mode_exits_with_modeexit_with_args(self, mode0: Mode):
        with mode0:
            testval = 3
            raise ModeExit("FOOO")
            testval = 0  # type: ignore # (never hit)

        assert testval == 3

    def test_mode_exits_with_other_exception(self, mode0: Mode):
        # Other exceptions are passed through
        class MyException(Exception): ...

        with pytest.raises(MyException):
            with mode0:
                testval = 4
                raise MyException
                testval = 0  # type: ignore # (never hit)

        assert testval == 4


class TestHandleActivationFail:
    """Tests for handle_activation_fail"""

    @staticmethod
    @pytest.fixture
    def result1():
        return ActivationResult(modename="testmode")

    @staticmethod
    @pytest.fixture
    def error_text_match(result1):
        return re.escape(result1.get_error_text())

    def test_pass(self, result1):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            handle_activation_fail(on_fail="pass", result=result1)

    def test_warn(self, result1, error_text_match):
        with pytest.warns(UserWarning, match=error_text_match):
            handle_activation_fail(on_fail="warn", result=result1)

    def test_error(self, result1, error_text_match):
        with pytest.raises(ActivationError, match=error_text_match):
            handle_activation_fail(on_fail="error", result=result1)

    def test_callable(self, result1):
        mock = Mock()
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            handle_activation_fail(on_fail=mock, result=result1)
        mock.assert_called_once_with(result1)

    def test_bad_on_fail_value(self, result1):
        with pytest.raises(ValueError, match="on_fail must be one of"):
            handle_activation_fail(
                on_fail="foo",  # type: ignore
                result=result1,
            )


@pytest.mark.usefixtures("provide_methods_a_f")
class TestSelectMethods:

    def test_filter_with_blacklist(self):

        (MethodB, MethodD, MethodE) = get_methods(["B", "D", "E"])
        methods = [MethodB, MethodD, MethodE]
        assert select_methods(methods, omit=["B"]) == [MethodD, MethodE]
        assert select_methods(methods, omit=["B", "E"]) == [MethodD]

    def test_extra_omit_does_not_matter(self):
        (MethodB, MethodD, MethodE) = get_methods(["B", "D", "E"])
        methods = [MethodB, MethodD, MethodE]
        # Extra 'omit' methods do not matter
        assert select_methods(methods, omit=["B", "E", "foo", "bar"]) == [
            MethodD,
        ]

    def test_filter_with_a_whitelist(self):
        (MethodB, MethodD, MethodE) = get_methods(["B", "D", "E"])
        methods = [MethodB, MethodD, MethodE]
        assert select_methods(methods, use_only=["B", "E"]) == [MethodB, MethodE]

    def test_whitelist_extras_causes_exception(self):

        (MethodB, MethodD, MethodE) = get_methods(["B", "D", "E"])
        methods = [MethodB, MethodD, MethodE]

        # If a whitelist contains extra methods, raise exception
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Methods ['bar', 'foo'] in `use_only` are not part of `methods`!"
            ),
        ):
            select_methods(methods, use_only=["foo", "bar"])

    def test_cannot_provide_omit_and_use_only(self):

        (MethodB, MethodD, MethodE) = get_methods(["B", "D", "E"])
        methods = [MethodB, MethodD, MethodE]
        # Cannot provide both: omit and use_only
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Can only define omit (blacklist) or use_only (whitelist), not both!"
            ),
        ):
            select_methods(methods, use_only=["B"], omit=["E"])


# These are the only "falsy" values for WAKEPY_FAKE_SUCCESS
FALSY_TEST_VALUES = (None, "0", "no", "NO", "False", "false", "FALSE")
TRUTHY_TEST_VALUES = ("1", "yes", "True", "anystring")


class TestAddFakeSuccessIfRequired:

    @pytest.mark.parametrize("val", FALSY_TEST_VALUES)
    def test_falsy_values(self, val, methods_abc: List[Type[Method]]):
        assert add_fake_success_if_required(methods_abc, val) == methods_abc

    @pytest.mark.parametrize("val", TRUTHY_TEST_VALUES)
    def test_truthy_values(self, val, methods_abc: List[Type[Method]]):
        [MethodA, MethodB, MethodC] = methods_abc
        # If the value is truthy, add the fake success method to the
        # beginning of the input method list
        assert add_fake_success_if_required(methods_abc, val) == [
            get_method(WAKEPY_FAKE_SUCCESS),
            MethodA,
            MethodB,
            MethodC,
        ]


class TestShouldFakeSuccess:

    @pytest.mark.parametrize("val", FALSY_TEST_VALUES)
    def test_falsy_values(self, val):
        assert should_fake_success(val) is False

    @pytest.mark.parametrize("val", TRUTHY_TEST_VALUES)
    def test_truthy_values(self, val):
        assert should_fake_success(val) is True


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
            "wakepy.core.prioritization._check_methods_priority",
            mocks._check_methods_priority,
        )
        monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "0")
        return mocks
