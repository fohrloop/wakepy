import pytest

from wakepy.modes import keep
from wakepy.core import ModeName, Method


def create_methods(monkeypatch, name_prefix: str, modename: ModeName):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

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


def test_keep_running_mode_creation(monkeypatch):
    name_prefix = "running"
    MethodA, MethodB, MethodC = create_methods(
        monkeypatch, name_prefix=name_prefix, modename=ModeName.KEEP_RUNNING
    )

    mode = keep.running()

    # All the methods for the mode are selected automatically
    assert set(mode.methods) == {MethodA, MethodB, MethodC}

    # Case: Test "omit" parameter
    mode = keep.running(omit=[f"{name_prefix}A"])
    assert set(mode.methods) == {MethodB, MethodC}

    # Case: Test "methods" parameter
    mode = keep.running(methods=[f"{name_prefix}A", f"{name_prefix}B"])
    assert set(mode.methods) == {MethodB, MethodA}


@pytest.mark.skip("This waits to be fixed")
def test_keep_running():
    with keep.running() as k:
        assert k.success
        assert not k.failure


@pytest.mark.skip("This waits to be fixed")
def test_keep_presenting():
    with keep.presenting() as k:
        assert k.success
        assert not k.failure
