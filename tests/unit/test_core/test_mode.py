from unittest.mock import Mock, call

import pytest

from wakepy.core.activationmanager import ModeActivationManager
from wakepy.core.method import Method
from wakepy.core.mode import ActivationResult, Mode, ModeExit


def mocks_for_test_mode():
    # Setup test
    mocks = Mock()

    manager_cls = Mock(spec_set=type(ModeActivationManager))
    manager = Mock(spec_set=ModeActivationManager)
    result = Mock(spec_set=ActivationResult)
    methods = [Mock(spec_set=type(Method)) for _ in range(3)]
    prioritize = methods[::-1]

    dbus_adapter = Mock()

    manager_cls.return_value = manager
    manager.activate.return_value = result

    # Record calls in a "mock manager"
    mocks.manager_cls = manager_cls
    mocks.manager = manager
    mocks.result = result
    mocks.methods = methods
    mocks.dbus_adapter = dbus_adapter
    mocks.prioritize = prioritize
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
        _manager_class = mocks.manager_cls

    # starting point: No mock calls
    assert mocks.mock_calls == []

    mode = TestMode(
        mocks.methods, prioritize=mocks.prioritize, dbus_adapter=mocks.dbus_adapter
    )

    # Here we have one call. During init, the ModeActivationManager
    # instance is created
    assert len(mocks.mock_calls) == 1

    # We have now created a new manager instance
    assert mocks.mock_calls[0] == call.manager_cls(dbus_adapter=mocks.dbus_adapter)

    # Test that the context manager protocol works
    with mode as m:
        # The second call
        # We have also called activate
        assert len(mocks.mock_calls) == 2
        assert mocks.mock_calls[1] == call.manager_cls().activate(
            methods=mocks.methods, prioritize=mocks.prioritize
        )
        # The __enter__ returns the value from the manager.activate()
        # call
        assert m == mocks.result

    # If we get here, the __exit__ works without errors
    # manager.deactivate() is called during __exit__
    assert len(mocks.mock_calls) == 3
    assert mocks.mock_calls[2] == call.manager_cls().deactivate()


def get_mocks_and_testmode():
    # Setup mocks
    mocks = mocks_for_test_mode()

    class TestMode(Mode):
        _manager_class = mocks.manager_cls

    return mocks, TestMode


def test_mode_exits():
    mocks, TestMode = get_mocks_and_testmode()

    # Normal exit
    with TestMode(mocks.methods):
        testval = 1

    assert testval == 1

    # The deactivate is also called!
    assert mocks.mock_calls == [
        call.manager_cls(dbus_adapter=None),
        call.manager_cls().activate(methods=mocks.methods, prioritize=None),
        call.manager_cls().deactivate(),
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
    assert mocks.mock_calls == [
        call.manager_cls(dbus_adapter=None),
        call.manager_cls().activate(methods=mocks.methods, prioritize=None),
        call.manager_cls().deactivate(),
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
    assert mocks.mock_calls == [
        call.manager_cls(dbus_adapter=None),
        call.manager_cls().activate(methods=mocks.methods, prioritize=None),
        call.manager_cls().deactivate(),
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
    assert mocks.mock_calls == [
        call.manager_cls(dbus_adapter=None),
        call.manager_cls().activate(methods=mocks.methods, prioritize=None),
        call.manager_cls().deactivate(),
    ]
