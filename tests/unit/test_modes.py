import re

import pytest

from wakepy.core import ActivationResult, DbusAdapter, Method, Mode, ModeName
from wakepy.modes import keep
from wakepy import ActivationError


@pytest.mark.parametrize(
    "input_args",
    [
        dict(
            name_prefix="running",
            function_under_test=keep.running,
            modename=ModeName.KEEP_RUNNING,
        ),
        dict(
            name_prefix="presenting",
            function_under_test=keep.presenting,
            modename=ModeName.KEEP_PRESENTING,
        ),
    ],
)
def test_keep_running_mode_creation(input_args, monkeypatch, testutils):
    """Simple test for keep.running and keep.presenting. Tests that all input
    arguments for the functions are passed to the Mode.__init__
    """

    testutils.empty_method_registry(monkeypatch)

    name_prefix = input_args["name_prefix"]
    function_under_test = input_args["function_under_test"]
    modename = input_args["modename"]

    class MethodA(Method):
        name = f"{name_prefix}A"
        mode = modename

    class MethodB(Method):
        name = f"{name_prefix}B"
        mode = modename

    class MethodC(Method):
        name = f"{name_prefix}C"
        mode = modename

    mode = function_under_test()
    # All the methods for the mode are selected automatically
    assert set(mode.methods_classes) == {MethodA, MethodB, MethodC}

    # Case: Test "omit" parameter
    mode = function_under_test(omit=[f"{name_prefix}A"])
    assert set(mode.methods_classes) == {MethodB, MethodC}

    # Case: Test "methods" parameter
    mode = function_under_test(methods=[f"{name_prefix}A", f"{name_prefix}B"])
    assert set(mode.methods_classes) == {MethodB, MethodA}

    # Case: Test "methods_priority" parameter
    methods_priority = [f"{name_prefix}A", f"{name_prefix}B"]
    mode = function_under_test(methods_priority=methods_priority)
    assert mode.methods_priority == methods_priority
    assert set(mode.methods_classes) == {MethodB, MethodA, MethodC}

    # Case: Test "dbus_adapter" parameter
    class MyDbusAdapter(DbusAdapter):
        ...

    mode = function_under_test(dbus_adapter=MyDbusAdapter)
    assert mode._dbus_adapter_cls == MyDbusAdapter


def test_keep_running_with_fake_success(monkeypatch, fake_dbus_adapter):
    """Simple smoke test for keep.running()"""
    monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "1")
    mode = keep.running(dbus_adapter=fake_dbus_adapter)
    assert mode.active is False

    with mode as m:
        assert mode is m
        assert m.active is True
        assert m.activation_result.success is True

    assert m.active is False
    assert isinstance(m.activation_result, ActivationResult)


def test_keep_presenting(monkeypatch, fake_dbus_adapter):
    """Simple smoke test for keep.presenting()"""
    monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "1")
    with keep.presenting(dbus_adapter=fake_dbus_adapter) as m:
        assert isinstance(m, Mode)
        assert m.activation_result.success is True


@pytest.mark.parametrize(
    "modefactory, expected_name",
    [
        (keep.running, "keep.running"),
        (keep.presenting, "keep.presenting"),
    ],
)
class TestOnFail:
    """Test failure handling for keep.presenting and keep.running."""

    def test_on_fail_pass(self, modefactory, expected_name):
        with modefactory(methods=[], on_fail="pass") as m:
            self._assertions_for_activation_failure(m, expected_name)

    def test_on_fail_warn(self, modefactory, expected_name):
        err_txt = f'Could not activate Mode "{expected_name}"!'
        with pytest.warns(UserWarning, match=re.escape(err_txt)):
            with modefactory(methods=[], on_fail="warn") as m:
                self._assertions_for_activation_failure(m, expected_name)

    def test_on_fail_error(self, modefactory, expected_name):
        err_txt = f'Could not activate Mode "{expected_name}"!'
        with pytest.raises(ActivationError, match=re.escape(err_txt)):
            with modefactory(methods=[], on_fail="error") as m:
                self._assertions_for_activation_failure(m, expected_name)

    def test_on_fail_callable(self, modefactory, expected_name):
        called = False

        def my_callable(result):
            nonlocal called
            called = True
            assert isinstance(result, ActivationResult)

        with modefactory(methods=[], on_fail=my_callable) as m:
            assert called is True
            self._assertions_for_activation_failure(m, expected_name)

    @staticmethod
    def _assertions_for_activation_failure(m: Mode, expected_name):
        assert m.active is False
        assert isinstance(m, Mode)
        assert m.name == expected_name
        assert m.activation_result.modename == expected_name
