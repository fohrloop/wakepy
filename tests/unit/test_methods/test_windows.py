import re
import sys
from unittest.mock import patch

import pytest

if sys.platform != "win32":
    pytest.skip(allow_module_level=True)

import wakepy.methods.windows as windows  # type: ignore[unreachable, unused-ignore]
from wakepy.methods.windows import (
    ES_CONTINUOUS,
    ES_DISPLAY_REQUIRED,
    ES_SYSTEM_REQUIRED,
    WindowsKeepPresenting,
    WindowsKeepRunning,
)

windows._release_event_timeout = 0.001
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

        def set_thread_execution_state(flags):
            assert flags == expected_flag
            return flags

        with patch(
            "wakepy.methods.windows.ctypes.windll.kernel32.SetThreadExecutionState",
            set_thread_execution_state,
        ):
            retval = method.enter_mode()

        assert retval is None

    @pytest.mark.parametrize(
        "method_cls",
        [WindowsKeepPresenting, WindowsKeepRunning],
    )
    def test_exit_mode_success(self, method_cls):
        method = method_cls()
        # prepare: enter the mode
        with patch(
            "wakepy.methods.windows.ctypes.windll.kernel32.SetThreadExecutionState",
            lambda x: x,
        ):
            method.enter_mode()

        def set_thread_execution_state(flags):
            assert flags == ES_CONTINUOUS
            return flags

        with patch(
            "wakepy.methods.windows.ctypes.windll.kernel32.SetThreadExecutionState",
            set_thread_execution_state,
        ):
            retval = method.exit_mode()

        assert retval is None

    @pytest.mark.parametrize(
        "method_cls",
        [WindowsKeepPresenting, WindowsKeepRunning],
    )
    def test_enter_mode_with_exception(self, method_cls):
        method = method_cls()

        def raising_exc(_):
            raise AttributeError("foo")

        with patch(
            "wakepy.methods.windows.ctypes.windll.kernel32.SetThreadExecutionState",
            raising_exc,
        ):
            with pytest.raises(RuntimeError, match="Could not use kernel32.dll!"):
                method.enter_mode()

    @pytest.mark.parametrize(
        "method_cls",
        [WindowsKeepPresenting, WindowsKeepRunning],
    )
    def test_exit_mode_with_exception(self, method_cls):
        method = method_cls()

        with patch(
            "wakepy.methods.windows.ctypes.windll.kernel32.SetThreadExecutionState",
            lambda x: x,
        ):
            method.enter_mode()

        def raising_exc(_):
            raise AttributeError("foo")

        with patch(
            "wakepy.methods.windows.ctypes.windll.kernel32.SetThreadExecutionState",
            raising_exc,
        ):
            with pytest.raises(RuntimeError, match="Could not use kernel32.dll!"):
                method.exit_mode()

    @pytest.mark.parametrize(
        "method_cls",
        [WindowsKeepPresenting, WindowsKeepRunning],
    )
    def test_exit_mode_with_bad_return_value_from_thread(self, method_cls):
        method = method_cls()

        with patch(
            "wakepy.methods.windows.ctypes.windll.kernel32.SetThreadExecutionState",
            lambda x: x,
        ):
            method.enter_mode()

        # returning 0 means returning NULL (error in SetThreadExecutionState
        # call)
        with patch(
            "wakepy.methods.windows.ctypes.windll.kernel32.SetThreadExecutionState",
            lambda x: 0,
        ):
            with pytest.raises(
                RuntimeError, match="SetThreadExecutionState returned NULL"
            ):
                method.exit_mode()

    @pytest.mark.parametrize(
        "method_cls",
        [WindowsKeepPresenting, WindowsKeepRunning],
    )
    def test_exit_mode_before_enter(self, method_cls):
        # does not make much practical sense but required for test coverage
        method = method_cls()
        # need to add something to the queue; otherwise would wait until an
        # exception
        method._queue_from_thread.put(1)
        method.exit_mode()
        assert method._inhibiting_thread is None

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
    def test_wrong_return_type_from_set_thread_execution_state(
        self, method_cls, expected_flag
    ):
        method = method_cls()

        def set_thread_execution_state(flags):
            return "foo"

        with patch(
            "wakepy.methods.windows.ctypes.windll.kernel32.SetThreadExecutionState",
            set_thread_execution_state,
        ):
            with pytest.raises(
                RuntimeError,
                match=re.escape("Unknown result type: <class 'str'> (foo)"),
            ):
                method.enter_mode()
