import pytest

from wakepy.core import ActivationResult, DbusAdapter, Method, Mode, ModeName
from wakepy.modes import keep


def create_methods(monkeypatch, name_prefix: str, modename: ModeName):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method._method_registry", dict())

    class MethodA(Method):
        name = f"{name_prefix}A"
        mode = modename

    class MethodB(Method):
        name = f"{name_prefix}B"
        mode = modename

    class MethodC(Method):
        name = f"{name_prefix}C"
        mode = modename

    return MethodA, MethodB, MethodC


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
def test_keep_running_mode_creation(input_args, monkeypatch):
    """Simple test for keep.running and keep.presenting. Tests that all input
    arguments for the functions are passed to the Mode.__init__
    """
    name_prefix = input_args["name_prefix"]
    function_under_test = input_args["function_under_test"]

    MethodA, MethodB, MethodC = create_methods(
        monkeypatch, name_prefix=name_prefix, modename=input_args["modename"]
    )

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


def test_keep_running_without_fake_success(monkeypatch, fake_dbus_adapter):
    """Simple smoke test for keep.running()"""
    monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "0")
    # This we expect to fail as the only adapter is the fake_dbus_adapter
    mode = keep.running(dbus_adapter=fake_dbus_adapter)
    assert mode.active is False

    with mode as m:
        assert mode is m
        assert m.active is False
        assert m.activation_result.success is False

    assert m.active is False
    assert isinstance(m.activation_result, ActivationResult)


def test_keep_presenting(fake_dbus_adapter):
    """Simple smoke test for keep.presenting()"""
    with keep.presenting(dbus_adapter=fake_dbus_adapter) as m:
        assert isinstance(m, Mode)
        assert isinstance(m.activation_result.success, bool)
