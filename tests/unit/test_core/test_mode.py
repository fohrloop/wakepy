from __future__ import annotations

import copy
import re
import threading
import typing
import warnings
from unittest.mock import Mock

import pytest

from tests.unit.test_core.testmethods import get_test_method_class
from wakepy import (
    ActivationError,
    ActivationResult,
    ContextAlreadyEnteredError,
    Method,
    MethodInfo,
    Mode,
)
from wakepy.core import PlatformType
from wakepy.core.activationresult import MethodActivationResult
from wakepy.core.constants import WAKEPY_FAKE_SUCCESS, StageName
from wakepy.core.dbus import DBusAdapter
from wakepy.core.heartbeat import Heartbeat
from wakepy.core.mode import (
    ModeExit,
    ThreadSafetyWarning,
    UnrecognizedMethodNames,
    _ModeParams,
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
    testutils.empty_method_registry(monkeypatch)

    class TestMethod(Method):
        supported_platforms = (PlatformType.ANY,)

    class MethodA(TestMethod):
        name = "MethodA"
        mode_name = "foo"

        def enter_mode(self): ...

    class MethodB(TestMethod):
        name = "MethodB"
        mode_name = "foo"

        def enter_mode(self): ...

    class MethodC(TestMethod):
        name = "MethodC"
        mode_name = "foo"

        def enter_mode(self): ...

    return [MethodA, MethodB, MethodC]


@pytest.fixture
def methods_priority0():
    return ["*"]


@pytest.fixture
def mode0(
    methods_abc: List[Type[Method]],
    testmode_cls: Type[Mode],
    methods_priority0: List[str],
) -> Mode:
    params = _ModeParams(
        name="TestMode",
        method_classes=methods_abc,
        dbus_adapter=None,
        methods_priority=methods_priority0,
    )
    return testmode_cls(params)


@pytest.fixture
def mode1_with_dbus(
    methods_abc: List[Type[Method]],
    testmode_cls: Type[Mode],
    methods_priority0: List[str],
    dbus_adapter_cls: Type[DBusAdapter],
):
    params = _ModeParams(
        name="TestMode1",
        method_classes=methods_abc,
        methods_priority=methods_priority0,
        dbus_adapter=dbus_adapter_cls,
    )
    return testmode_cls(params)


class TestModeContextManager:

    @pytest.mark.usefixtures("WAKEPY_FAKE_SUCCESS_eq_1")
    def test_mode_contextmanager_protocol(
        self,
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
            # There is an ActivationResult available in .result
            assert isinstance(m.result, ActivationResult)
            # The active method is also available
            assert isinstance(mode0._active_method, Method)

            activation_result = copy.deepcopy(m.result)
            flag_end_of_with_block = True

        # reached the end of the with block
        assert flag_end_of_with_block

        # After exiting the mode, Mode.active is set to False
        assert m.active is False
        # The active_method is set to None
        assert m.active_method is None
        # The activation result is still there (not removed during
        # deactivation)
        assert activation_result == m.result

    @pytest.mark.usefixtures("WAKEPY_FAKE_SUCCESS_eq_1")
    def test_no_methods_succeeds_when_using_fake_success(
        self,
    ):
        # This will not fail as when the Mode is activated, the
        # WakepyFakeSuccess method is added to the list of used methods.
        params = _ModeParams(method_classes=[])
        with Mode(params):
            ...


class TestModeActiveAndUsedMethod:
    """Test the .active_method and .method attributes"""

    def test_simple(self, methods_abc):
        [MethodA, MethodB, _] = methods_abc
        params = _ModeParams(method_classes=[MethodA, MethodB])
        mode = Mode(params)

        method_info_a = MethodInfo._from_method(MethodA())

        # before activated, active and used methods are None
        assert mode.active_method is None
        assert mode.method is None

        with mode:
            # When mode is active, active and used methods are same.
            assert mode.active_method == method_info_a
            assert mode.method == method_info_a

        # when mode is not active, active method is None, but used method is
        # the one used previously.
        assert mode.active_method is None
        assert mode.method == method_info_a


@pytest.mark.usefixtures("WAKEPY_FAKE_SUCCESS_eq_1")
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
                mode0._active_method = None

        # Need to manually cleanup after this test, as otherwise the global
        # state will not be correct. As said, this should never ever happen
        # in a real life situation.
        mode0._unset_current_mode()

    def test_unset_before_activate(
        self,
        mode0: Mode,
    ):
        with pytest.raises(
            RuntimeError,
            match="Cannot unset current mode, because it was never set! ",
        ):
            mode0._unset_current_mode()

    def test_activate_twice_without_deactivation(
        self,
        mode0: Mode,
    ):
        # It should not be possible to activate a mode twice without
        # deactivating it first.
        with mode0 as m:
            with pytest.raises(
                ContextAlreadyEnteredError,
                match="A Mode can only be activated once!.*",
            ):
                with m:
                    ...


@pytest.mark.usefixtures("WAKEPY_FAKE_SUCCESS_eq_1")
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
        return ActivationResult([], mode_name="testmode")

    @staticmethod
    @pytest.fixture
    def error_text_match(result1):
        return re.escape(result1.get_failure_text())

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
            UnrecognizedMethodNames,
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
FALSY_TEST_VALUES = (
    None,
    "0",
    "no",
    "NO",
    "N",
    "n",
    "False",
    "false",
    "FALSE",
    "F",
    "f",
    "",
)
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


class TestActivateOneOfMethods:
    """tests for Mode._activate_one_of_methods"""

    def test_activate_without_methods(self):
        # Act
        res, active_method, heartbeat = Mode._activate_one_of_methods(
            [], dbus_adapter=None
        )

        # Assert
        assert res == []
        assert active_method is None
        assert heartbeat is None

    def test_activate_function_success(self):

        # Setup
        methodcls_fail = get_test_method_class(enter_mode=Exception("error"))
        methodcls_success = get_test_method_class(enter_mode=None)

        # Act
        res, active_method, heartbeat = Mode._activate_one_of_methods(
            [methodcls_success, methodcls_fail],
        )
        # Assert
        assert len(res) == 2
        assert res == [
            MethodActivationResult(
                method=MethodInfo._from_method(methodcls_success()),
                success=True,
            ),
            MethodActivationResult(
                method=MethodInfo._from_method(methodcls_fail()),
                success=None,
            ),
        ]
        assert isinstance(active_method, methodcls_success)
        assert heartbeat is None

    def test_activate_function_success_with_heartbeat(self):

        # Setup
        methodcls_success_with_hb = get_test_method_class(
            enter_mode=None, heartbeat=None
        )

        # Act
        res, active_method, heartbeat = Mode._activate_one_of_methods(
            [methodcls_success_with_hb],
        )

        # Assert
        # The activation succeeded, and the method has heartbeat, so the
        # heartbeat must be instance of Heartbeate
        assert res == [
            MethodActivationResult(
                method=MethodInfo._from_method(methodcls_success_with_hb()),
                success=True,
            )
        ]
        assert isinstance(active_method, methodcls_success_with_hb)
        assert isinstance(heartbeat, Heartbeat)

    def test_activate_function_failure(self):
        # Setup
        exc = Exception("error")
        methodcls_fail = get_test_method_class(enter_mode=exc)

        # Act
        res, active_method, heartbeat = Mode._activate_one_of_methods([methodcls_fail])

        # Assert
        # The activation failed, so active_method and heartbeat is None
        assert res == [
            MethodActivationResult(
                method=MethodInfo._from_method(methodcls_fail()),
                success=False,
                failure_stage=StageName.ACTIVATION,
                failure_reason=repr(exc),
            )
        ]
        assert active_method is None
        assert heartbeat is None
        assert heartbeat is None


def test_use_mode_in_separate_thread(mode0: Mode):
    """Modes should be only used in the thread they were created in.
    Test that using a Mode in a different thread issues a Warning."""

    # Setup
    def func():
        with pytest.warns(ThreadSafetyWarning):
            with mode0:
                ...

    t = threading.Thread(target=func)

    # Act and Assert
    t.start()

    # Cleanup
    t.join()
