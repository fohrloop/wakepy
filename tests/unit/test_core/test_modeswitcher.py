import queue

import pytest
from testmethods import MethodIs, get_method_class

from wakepy.core.method import EnterModeError, ExitModeError

pytest.skip("These need to be fixed", allow_module_level=True)

ModeManager._timeout_maximum = 0.1  # make tests fail faster


def test_mode_switch_thread():
    method_ok = get_method_class(
        enter_mode=MethodIs.SUCCESSFUL,
        exit_mode=MethodIs.SUCCESSFUL,
    )()

    q_in, q_out = queue.Queue(), queue.Queue()
    thread = ModeWorkerThread([method_ok], queue_in=q_in, queue_out=q_out)

    thread.run()
    ans = q_out.get(block=True, timeout=1)

    assert ans == ("OK", None)
    raise NotImplementedError("test WIP")


def test_mode_switcher_two_methods():
    """Test normal (OK case) mode switching with two methods"""
    method_ok = get_method_class(heartbeat=MethodIs.SUCCESSFUL)()
    method_ok2 = get_method_class(
        enter_mode=MethodIs.SUCCESSFUL,
        heartbeat=MethodIs.SUCCESSFUL,
        exit_mode=MethodIs.SUCCESSFUL,
    )()

    manager = ModeManager([method_ok, method_ok2])
    manager.run()

    assert manager.successful_methods == [method_ok.name, method_ok2.name]
    assert manager.failed_methods == []
    assert manager.exceptions == []


def test_failing_method_during_enter_mode(test_method_classes):
    """Test mode switching when tere is one method that fails during enter_mode()"""
    method_ok = test_method_classes["M010"]()
    method_ok2 = test_method_classes["M111"]()

    # This has exception in the method.enter_mode() -> EnterModeError
    method_cause_exception1 = test_method_classes["M201"]()

    manager = ModeManager([method_ok, method_cause_exception1, method_ok2])
    manager.run()

    assert manager.successful_methods == [m.name for m in [method_ok, method_ok2]]
    assert manager.failed_methods == [method_cause_exception1.name]
    assert len(manager.exceptions) == 1
    assert isinstance(manager.exceptions[0], EnterModeError)


def test_mode_switcher_with_exception_caused_by_method(test_method_classes):
    # This causes ExitModeError
    method_cause_exception1 = test_method_classes["M122"]()

    manager = ModeManager([method_cause_exception1])

    with pytest.raises(RuntimeError) as exc_info:
        manager.run()
        manager.success

    assert "Error during switching to a mode." in str(exc_info.value)
    assert isinstance(exc_info.value.__cause__, ExitModeError)


def test_mode_switcher_with_exception(monkeypatch):
    """In this test, there is some general, unknown exception in
    ModeWorkerThread.try_mode_switch (forced by monkeypatching).
    Make sure that this situation is handled correctly.
    """

    method_ok = get_method_class(
        enter_mode=MethodIs.SUCCESSFUL,
        exit_mode=MethodIs.SUCCESSFUL,
    )()

    def bad_func():
        raise Exception

    monkeypatch.setattr(ModeWorkerThread, "try_mode_switch", bad_func)

    manager = ModeManager([method_ok])

    with pytest.raises(RuntimeError) as exc_info:
        manager.run()
        manager.success

    assert "Error during switching to a mode." in str(exc_info.value)
    # This one is from the full traceback:
    assert "bad_func()" in str(exc_info.value.__cause__)
