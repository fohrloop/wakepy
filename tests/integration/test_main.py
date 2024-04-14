"""Integration tests for the __main__ CLI"""

from unittest.mock import Mock, call, patch

import pytest

from wakepy.__main__ import _get_activation_error_text, get_startup_text, main
from wakepy.core import CURRENT_PLATFORM, ActivationResult, Method


@pytest.fixture
def modename_working():
    return "testmode_working"


@pytest.fixture
def modename_broken():
    return "testmode_broken"


@pytest.fixture
def method1(modename_working):
    class WorkingMethod(Method):
        """This is a succesful method as it implements enter_mode which returns
        None"""

        name = "method1"
        mode = modename_working
        supported_platforms = (CURRENT_PLATFORM,)

        def enter_mode(self) -> None:
            return

    return WorkingMethod


@pytest.fixture
def method2_broken(modename_broken):
    class BrokenMethod(Method):
        """This is a unsuccesful method as it implements enter_mode which
        raises an Exception"""

        name = "method2_broken"
        mode = modename_broken
        supported_platforms = (CURRENT_PLATFORM,)

        def enter_mode(self) -> None:
            raise RuntimeError("foo")

    return BrokenMethod


@patch("wakepy.__main__.wait_until_keyboardinterrupt")
@patch("wakepy.__main__.parse_arguments")
class TestMain:
    """Tests the main() function from the __main__.py in a simple way. This
    is more of a smoke test. The functionality of the different parts is
    already tested in unit tests."""

    def test_working_mode(
        self,
        parse_arguments,
        wait_until_keyboardinterrupt,
        method1,
    ):

        with patch("sys.argv", self.sys_argv), patch("builtins.print") as print_mock:
            manager = self.setup_mock_manager(
                method1, print_mock, parse_arguments, wait_until_keyboardinterrupt
            )
            main()

        assert manager.mock_calls == [
            call.print(get_startup_text(method1.mode)),
            call.wait_until_keyboardinterrupt(),
            call.print("\n\nExited."),
        ]

    @pytest.mark.usefixtures("method2_broken")
    def test_non_working_mode(
        self,
        parse_arguments,
        wait_until_keyboardinterrupt,
        method2_broken,
    ):

        with patch("sys.argv", self.sys_argv), patch("builtins.print") as print_mock:
            manager = self.setup_mock_manager(
                method2_broken,
                print_mock,
                parse_arguments,
                wait_until_keyboardinterrupt,
            )
            main()

        expected_result = ActivationResult(results=[], modename=method2_broken.mode)
        assert manager.mock_calls == [
            call.print(get_startup_text(method2_broken.mode)),
            call.print(_get_activation_error_text(expected_result)),
        ]

    @staticmethod
    def setup_mock_manager(
        method: Method,
        print_mock,
        parse_arguments,
        wait_until_keyboardinterrupt,
    ):
        # Assume that user has specified some mode in the commandline which
        # resolves to `method.mode`
        parse_arguments.return_value = method.mode

        mocks = Mock()
        mocks.attach_mock(print_mock, "print")
        mocks.attach_mock(wait_until_keyboardinterrupt, "wait_until_keyboardinterrupt")
        return mocks

    @property
    def sys_argv(self):
        # The patched value for sys.argv. Does not matter here otherwise, but
        # should be a list of at least two items.
        return ["", ""]
