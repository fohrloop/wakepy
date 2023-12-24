from unittest.mock import Mock, call

import pytest

from wakepy.core.calls import CallProcessor
from wakepy.core.mode import ActivationResult, Mode, ModeController, ModeExit


def mocks_for_test_mode():
    # Setup test
    mocks = Mock()

    mocks.call_processor_cls = Mock()
    mocks.call_processor_cls.return_value = Mock(spec_set=CallProcessor)

    mocks.mode_controller_cls = Mock()
    mocks.mode_controller_cls.return_value = Mock(spec_set=ModeController)

    result = Mock(spec_set=ActivationResult)
    methods = [Mock() for _ in range(3)]

    # Record calls in a "mock manager"
    mocks.result = result
    mocks.methods = methods
    return mocks


def test_mode_contextmanager_protocol():
    """Test that the Mode fulfills the context manager protocol; i.e. it is
    possible to use instances of Mode in a with statement like this:

    with Mode() as m:
        ...

    Test also that the ModeActivationManager.activate() and .deactivate()
    are called as expected. and that the `m` is the return value of the
    manager.activate()
    """

    # Setup mocks
    mocks = mocks_for_test_mode()

    class TestMode(Mode):
        _call_processor_class = mocks.call_processor_class
        _controller_class = mocks.controller_class

    # starting point: No mock calls
    assert mocks.mock_calls == []

    mode = TestMode(mocks.methods, dbus_adapter=mocks.dbus_adapter)

    # No calls during init
    assert len(mocks.mock_calls) == 0

    # Test that the context manager protocol works
    with mode as m:
        # The second call
        # We have also called activate
        assert len(mocks.mock_calls) == 3

        # We have now created a new CallProcessor instance
        assert mocks.mock_calls[0] == call.call_processor_class(
            dbus_adapter=mocks.dbus_adapter
        )
        # We have also created a ModeController instance
        assert mocks.mock_calls[1] == call.controller_class(
            call_processor=mocks.call_processor_class.return_value
        )
        # And called ModeController.activate
        assert mocks.mock_calls[2] == call.controller_class().activate(
            mocks.methods, methods_priority=None
        )
        # The __enter__ returns the value from the ModeController.activate()
        # call
        assert m == mocks.controller_class.return_value.activate.return_value

    # If we get here, the __exit__ works without errors
    # ModeController.deactivate() is called during __exit__
    assert len(mocks.mock_calls) == 4
    assert mocks.mock_calls[3] == call.controller_class().deactivate()


def get_mocks_and_testmode():
    # Setup mocks
    mocks = mocks_for_test_mode()

    class TestMode(Mode):
        _call_processor_class = mocks.call_processor_class
        _controller_class = mocks.controller_class

    return mocks, TestMode


def test_mode_exits():
    mocks, TestMode = get_mocks_and_testmode()

    # Normal exit
    with TestMode(mocks.methods):
        testval = 1

    assert testval == 1

    # The deactivate is also called!
    assert mocks.mock_calls.copy() == [
        call.call_processor_class(dbus_adapter=None),
        call.controller_class(call_processor=mocks.call_processor_class()),
        call.controller_class().activate(mocks.methods, methods_priority=None),
        call.controller_class().deactivate(),
    ]


def test_mode_exits_with_modeexit():
    mocks, TestMode = get_mocks_and_testmode()

    # Exit with ModeExit
    with TestMode(mocks.methods):
        testval = 2
        raise ModeExit
        testval = 0  # never hit

    assert testval == 2

    # The deactivate is also called!
    assert mocks.mock_calls.copy() == [
        call.call_processor_class(dbus_adapter=None),
        call.controller_class(call_processor=mocks.call_processor_class()),
        call.controller_class().activate(mocks.methods, methods_priority=None),
        call.controller_class().deactivate(),
    ]


def test_mode_exits_with_modeexit_with_args():
    mocks, TestMode = get_mocks_and_testmode()

    # Exit with ModeExit with args
    with TestMode(mocks.methods):
        testval = 3
        raise ModeExit("FOOO")
        testval = 0  # never hit

    assert testval == 3

    # The deactivate is also called!
    assert mocks.mock_calls.copy() == [
        call.call_processor_class(dbus_adapter=None),
        call.controller_class(call_processor=mocks.call_processor_class()),
        call.controller_class().activate(mocks.methods, methods_priority=None),
        call.controller_class().deactivate(),
    ]


def test_mode_exits_with_other_exception():
    mocks, TestMode = get_mocks_and_testmode()

    # Other exceptions are passed through
    class MyException(Exception):
        ...

    with pytest.raises(MyException):
        with TestMode(mocks.methods):
            testval = 4
            raise MyException
            testval = 0

    assert testval == 4

    # The deactivate is also called!
    assert mocks.mock_calls.copy() == [
        call.call_processor_class(dbus_adapter=None),
        call.controller_class(call_processor=mocks.call_processor_class()),
        call.controller_class().activate(mocks.methods, methods_priority=None),
        call.controller_class().deactivate(),
    ]
