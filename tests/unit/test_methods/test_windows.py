from unittest.mock import patch

import pytest

from wakepy.methods.windows import (
    ES_CONTINUOUS,
    ES_DISPLAY_REQUIRED,
    ES_SYSTEM_REQUIRED,
    WindowsKeepPresenting,
    WindowsKeepRunning,
)

import wakepy.methods.windows as windows

windows._release_event_timeout = 1
"""Make tests *not* to wait forever"""
class TestWindowsSetThreadExecutionState:

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
    def test_enter_mode_success(self, method_cls, expected_flag):
        method = method_cls()

        with patch("wakepy.methods.windows.ctypes") as ctypesmock:
            retval = method.enter_mode()

        assert retval is None
        ctypesmock.windll.kernel32.SetThreadExecutionState.assert_called_with(
            expected_flag
        )

        # cleanup (otherwise will wait forever for the release event in the
        # inhibitor thread)
        with patch("wakepy.methods.windows.ctypes") as ctypesmock:
            method.exit_mode()

    @pytest.mark.parametrize(
        "method_cls",
        [WindowsKeepPresenting, WindowsKeepRunning],
    )
    def test_exit_mode_success(self, method_cls):
        method = method_cls()

        with patch("wakepy.methods.windows.ctypes") as ctypesmock:
            method.enter_mode()
            retval = method.exit_mode()

        assert retval is None
        ctypesmock.windll.kernel32.SetThreadExecutionState.assert_called_with(
            ES_CONTINUOUS
        )

    @pytest.mark.parametrize(
        "method_cls",
        [WindowsKeepPresenting, WindowsKeepRunning],
    )
    def test_enter_mode_with_exception(self, method_cls):
        method = method_cls()

        def raising_exc(_):
            raise AttributeError("foo")

        with patch("wakepy.methods.windows.ctypes") as ctypesmock:
            ctypesmock.windll.kernel32.SetThreadExecutionState.side_effect = raising_exc

            with pytest.raises(RuntimeError, match="Could not use kernel32.dll!"):
                method.enter_mode()

        # cleanup (otherwise will wait forever for the release event in the
        # inhibitor thread)
        with patch("wakepy.methods.windows.ctypes") as ctypesmock:
            method.exit_mode()

    @pytest.mark.parametrize(
        "method_cls",
        [WindowsKeepPresenting, WindowsKeepRunning],
    )
    def test_exit_mode_with_exception(self, method_cls):
        method = method_cls()

        with patch("wakepy.methods.windows.ctypes") as ctypesmock:
            method.enter_mode()

        def raising_exc(_):
            raise AttributeError("foo")

        with patch("wakepy.methods.windows.ctypes") as ctypesmock:
            ctypesmock.windll.kernel32.SetThreadExecutionState.side_effect = raising_exc

            with pytest.raises(RuntimeError, match="Could not use kernel32.dll!"):
                method.exit_mode()
