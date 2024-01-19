from unittest.mock import patch

import pytest

from wakepy.methods.windows import (
    ES_CONTINUOUS,
    ES_DISPLAY_REQUIRED,
    ES_SYSTEM_REQUIRED,
    WindowsKeepPresenting,
    WindowsKeepRunning,
)


@pytest.mark.parametrize(
    "method_cls, expected_flag",
    [
        (
            WindowsKeepPresenting,
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED,
        ),
        (WindowsKeepRunning, ES_CONTINUOUS | ES_SYSTEM_REQUIRED),
    ],
)
def test_enter_mode_success(method_cls, expected_flag):
    method = method_cls()

    with patch("wakepy.methods.windows.ctypes") as ctypesmock:
        retval = method.enter_mode()

    assert retval is None
    ctypesmock.windll.kernel32.SetThreadExecutionState.assert_called_with(expected_flag)


@pytest.mark.parametrize(
    "method_cls",
    [WindowsKeepPresenting, WindowsKeepRunning],
)
def test_exit_mode_success(method_cls):
    method = method_cls()

    with patch("wakepy.methods.windows.ctypes") as ctypesmock:
        retval = method.exit_mode()

    assert retval is None
    ctypesmock.windll.kernel32.SetThreadExecutionState.assert_called_with(ES_CONTINUOUS)


@pytest.mark.parametrize(
    "method_cls",
    [WindowsKeepPresenting, WindowsKeepRunning],
)
def test_enter_mode_with_exception(method_cls):
    method = method_cls()

    def raising_exc(_):
        raise AttributeError("foo")

    with patch("wakepy.methods.windows.ctypes") as ctypesmock:
        ctypesmock.windll.kernel32.SetThreadExecutionState.side_effect = raising_exc

        with pytest.raises(RuntimeError, match="Could not use kernel32.dll!"):
            method.enter_mode()


@pytest.mark.parametrize(
    "method_cls",
    [WindowsKeepPresenting, WindowsKeepRunning],
)
def test_exit_mode_with_exception(method_cls):
    method = method_cls()

    def raising_exc(_):
        raise AttributeError("foo")

    with patch("wakepy.methods.windows.ctypes") as ctypesmock:
        ctypesmock.windll.kernel32.SetThreadExecutionState.side_effect = raising_exc

        with pytest.raises(RuntimeError, match="Could not use kernel32.dll!"):
            method.exit_mode()
