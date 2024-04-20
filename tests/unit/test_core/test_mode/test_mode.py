from __future__ import annotations

import copy
import re
import typing
import warnings
from unittest.mock import Mock, call

import pytest

from tests.unit.test_core.testmethods import get_test_method_class
from wakepy import ActivationError, ActivationResult, Method, Mode
from wakepy.core.dbus import DBusAdapter
from wakepy.core.heartbeat import Heartbeat
from wakepy.core.mode import ModeExit, handle_activation_fail, select_methods
from wakepy.core.registry import get_methods

if typing.TYPE_CHECKING:
    from typing import List, Tuple, Type


def mocks_for_test_mode():
    # Setup test
    mocks = Mock()

    mocks.dbus_adapter_cls = Mock(spec_set=type(DBusAdapter))
    mocks.dbus_adapter_cls.return_value = Mock(spec_set=DBusAdapter)

    mocks.methods_priority = Mock()

    result = Mock(spec_set=ActivationResult)
    methods = [Mock() for _ in range(3)]

    # Record calls in a "mock manager"
    mocks.activation_result = result
    mocks.methods = methods
    return mocks


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
    dbus_adapter_cls: Type[DBusAdapter],
):
    return testmode_cls(
        methods_abc,
        methods_priority=methods_priority0,
        dbus_adapter=dbus_adapter_cls,
        name="TestMode",
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


class TestExitModeWithException:
    """Test cases when a Mode is exited with an Exception"""

    def test_mode_exits_with_modeexit(self, mode0):
        with mode0:
            testval = 2
            raise ModeExit
            testval = 0  # type: ignore # (never hit)

        assert testval == 2

    def test_mode_exits_with_modeexit_with_args(self, mode0):
        with mode0:
            testval = 3
            raise ModeExit("FOOO")
            testval = 0  # type: ignore # (never hit)

        assert testval == 3

    def test_mode_exits_with_other_exception(self, mode0):
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
