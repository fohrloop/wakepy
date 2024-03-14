from unittest.mock import Mock, call

import pytest
from testmethods import get_test_method_class

from wakepy.core.dbus import DBusAdapter
from wakepy.core.heartbeat import Heartbeat
from wakepy.core.mode import (
    ActivationResult,
    Mode,
    ModeController,
    ModeExit,
    handle_activation_fail,
)


def mocks_for_test_mode():
    # Setup test
    mocks = Mock()

    mocks.dbus_adapter_cls = Mock(spec_set=type(DBusAdapter))
    mocks.dbus_adapter_cls.return_value = Mock(spec_set=DBusAdapter)

    mocks.mode_controller_cls = Mock()
    mocks.mode_controller_cls.return_value = Mock(spec_set=ModeController)

    mocks.methods_priority = Mock()

    result = Mock(spec_set=ActivationResult)
    methods = [Mock() for _ in range(3)]

    # Record calls in a "mock manager"
    mocks.activation_result = result
    mocks.methods = methods
    return mocks


def get_mocks_and_testmode():
    # Setup mocks
    mocks = mocks_for_test_mode()

    class TestMode(Mode):
        _controller_class = mocks.controller_class

    return mocks, TestMode


def test_mode_contextmanager_protocol():
    """Test that the Mode fulfills the context manager protocol; i.e. it is
    possible to use instances of Mode in a with statement like this:

    with Mode() as m:
        ...

    Test also that the ModeController.activate() and .deactivate()
    are called as expected. and that the `m` is the return value of the
    manager.activate()
    """

    # Setup mocks
    mocks, TestMode = get_mocks_and_testmode()

    # starting point: No mock calls
    assert mocks.mock_calls == []

    mode = TestMode(
        mocks.methods,
        methods_priority=mocks.methods_priority,
        dbus_adapter=mocks.dbus_adapter_cls,
        name="TestMode",
    )

    # No calls during init
    assert len(mocks.mock_calls) == 0

    # Test that the context manager protocol works
    with mode as m:
        # The second call
        # We have also called activate
        assert len(mocks.mock_calls) == 3

        # We have also created a ModeController instance
        assert mocks.mock_calls[1] == call.controller_class(
            dbus_adapter=mocks.dbus_adapter_cls.return_value
        )
        # And called ModeController.activate
        assert mocks.mock_calls[2] == call.controller_class().activate(
            mocks.methods, methods_priority=mocks.methods_priority, modename="TestMode"
        )
        # The __enter__ returns the Mode
        assert m is mode

        # When activating, the .active is set to activation_result.success
        assert m.active is m.activation_result.success

        # The m.activation_result contains the value from the
        # ModeController.activate() call
        assert (
            m.activation_result
            == mocks.controller_class.return_value.activate.return_value
        )

    # After exiting the mode, Mode.active is set to False
    assert m.active is False

    # If we get here, the __exit__ works without errors
    # ModeController.deactivate() is called during __exit__
    assert len(mocks.mock_calls) == 4
    assert mocks.mock_calls[3] == call.controller_class().deactivate()


def test_mode_exits():
    mocks, TestMode = get_mocks_and_testmode()

    # Normal exit
    with TestMode(
        mocks.methods,
        methods_priority=mocks.methods_priority,
        dbus_adapter=mocks.dbus_adapter_cls,
    ) as mode:
        testval = 1

    assert testval == 1

    _assert_context_manager_used_correctly(mocks, mode)


def test_mode_exits_with_modeexit():
    mocks, TestMode = get_mocks_and_testmode()

    # Exit with ModeExit
    with TestMode(
        mocks.methods,
        methods_priority=mocks.methods_priority,
        dbus_adapter=mocks.dbus_adapter_cls,
    ) as mode:
        testval = 2
        raise ModeExit
        testval = 0  # never hit

    assert testval == 2

    _assert_context_manager_used_correctly(mocks, mode)


def test_mode_exits_with_modeexit_with_args():
    mocks, TestMode = get_mocks_and_testmode()

    # Exit with ModeExit with args
    with TestMode(
        mocks.methods,
        methods_priority=mocks.methods_priority,
        dbus_adapter=mocks.dbus_adapter_cls,
    ) as mode:
        testval = 3
        raise ModeExit("FOOO")
        testval = 0  # never hit

    assert testval == 3

    _assert_context_manager_used_correctly(mocks, mode)


def test_mode_exits_with_other_exception():
    mocks, TestMode = get_mocks_and_testmode()

    # Other exceptions are passed through
    class MyException(Exception): ...

    with pytest.raises(MyException):
        with TestMode(
            mocks.methods,
            methods_priority=mocks.methods_priority,
            dbus_adapter=mocks.dbus_adapter_cls,
        ) as mode:
            testval = 4
            raise MyException
            testval = 0

    assert testval == 4

    _assert_context_manager_used_correctly(mocks, mode)


def test_exiting_before_enter():

    mocks, TestMode = get_mocks_and_testmode()
    mode = TestMode(
        mocks.methods,
        methods_priority=mocks.methods_priority,
        dbus_adapter=mocks.dbus_adapter_cls,
    )
    with pytest.raises(RuntimeError, match="Must __enter__ before __exit__!"):
        mode.__exit__(None, None, None)


def _assert_context_manager_used_correctly(mocks, mode):
    assert mocks.mock_calls.copy() == [
        call.dbus_adapter_cls(),
        call.controller_class(dbus_adapter=mocks.dbus_adapter_cls.return_value),
        call.controller_class().activate(
            mocks.methods, methods_priority=mocks.methods_priority, modename=mode.name
        ),
        call.controller_class().deactivate(),
    ]


def test_handle_activation_fail_bad_on_fail_value():
    with pytest.raises(ValueError, match="on_fail must be one of"):
        handle_activation_fail(on_fail="foo", result=Mock(spec_set=ActivationResult))


def test_modecontroller(monkeypatch):
    # Disable fake success here, because we want to use method_cls for the
    # activation (and not WakepyFakeSuccess)
    monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "0")

    method_cls = get_test_method_class(enter_mode=None, heartbeat=None, exit_mode=None)
    controller = ModeController(Mock(spec_set=DBusAdapter))

    # When controller was created, it has not active method or heartbeat
    assert controller.active_method is None
    assert controller.heartbeat is None

    controller.activate([method_cls])
    assert isinstance(controller.active_method, method_cls)
    assert isinstance(controller.heartbeat, Heartbeat)

    retval = controller.deactivate()
    assert retval is True
    assert controller.active_method is None
    assert controller.heartbeat is None

    # Calling a deactivate for mode which is not activated will return False
    assert controller.deactivate() is False
