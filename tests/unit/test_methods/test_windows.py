import pytest
from unittest.mock import patch

from wakepy.methods.windows import (
    WindowsKeepPresenting,
    WindowsKeepRunning,
    ES_CONTINUOUS,
    ES_SYSTEM_REQUIRED,
    ES_DISPLAY_REQUIRED,
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
def test_windows_setthreadexecutionstate_enter_mode(method_cls, expected_flag):
    method = method_cls()

    with patch(
        "wakepy.methods.windows.ctypes",
    ) as ctypesmock:
        retval = method.enter_mode()

    assert retval is None
    ctypesmock.windll.kernel32.SetThreadExecutionState.assert_called_with(expected_flag)


@pytest.mark.parametrize(
    "method_cls",
    [WindowsKeepPresenting, WindowsKeepRunning],
)
def test_windows_setthreadexecutionstate_exit_mode(method_cls):
    method = method_cls()

    with patch(
        "wakepy.methods.windows.ctypes",
    ) as ctypesmock:
        retval = method.exit_mode()

    assert retval is None
    ctypesmock.windll.kernel32.SetThreadExecutionState.assert_called_with(ES_CONTINUOUS)
