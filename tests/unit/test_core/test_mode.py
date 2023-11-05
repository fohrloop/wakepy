from unittest.mock import Mock, call

from wakepy.core.mode import Mode, ActivationResult
from wakepy.core.modemanager import ModeActivationManager
from wakepy.core.method import Method


def mocks_for_test_mode():
    # Setup test
    mocks = Mock()

    manager_cls = Mock(spec_set=type(ModeActivationManager))
    manager = Mock(spec_set=ModeActivationManager)
    result = Mock(spec_set=ActivationResult)
    methods = [Mock(spec_set=type(Method)) for _ in range(3)]

    manager_cls.return_value = manager
    manager.activate.return_value = result

    # Record calls in a "mock manager"
    mocks.manager_cls = manager_cls
    mocks.manager = manager
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
    mode = Mode(mocks.methods)
    mode._manager_class = mocks.manager_cls

    # Test that the context manager protocol works

    # starting point: No mock calls
    assert mocks.mock_calls == []

    with mode as m:
        assert mocks.mock_calls == [
            # We have now created a new manager instance
            call.manager_cls(dbus_adapter=None),
            # We have also called activate
            call.manager_cls().activate(methods=mocks.methods),
        ]
        # The __enter__ returns the value from the manager.activate()
        # call
        assert m == mocks.result

    # If we get here, the __exit__ works without errors
    assert mocks.mock_calls[2] == call.manager_cls().deactivate()
    assert len(mocks.mock_calls) == 3
