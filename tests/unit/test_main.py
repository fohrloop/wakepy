"""Unit tests for the __main__ module"""

import sys
from unittest.mock import Mock, call, patch

import pytest

from wakepy import ActivationResult, Method
from wakepy.__main__ import (
    _get_activation_error_text,
    get_spinner_symbols,
    get_startup_text,
    handle_activation_error,
    main,
    parse_arguments,
    wait_until_keyboardinterrupt,
)
from wakepy.core import PlatformType
from wakepy.core.constants import IdentifiedPlatformType, ModeName


@pytest.fixture
def mode_name_working():
    return "testmode_working"


@pytest.fixture
def mode_name_broken():
    return "testmode_broken"


@pytest.fixture
def method1(mode_name_working):
    class WorkingMethod(Method):
        """This is a successful method as it implements enter_mode which
        returns None"""

        name = "method1"
        mode_name = mode_name_working
        supported_platforms = (PlatformType.ANY,)

        def enter_mode(self) -> None:
            return

    return WorkingMethod


@pytest.fixture
def method2_broken(mode_name_broken):
    class BrokenMethod(Method):
        """This is a unsuccessful method as it implements enter_mode which
        raises an Exception"""

        name = "method2_broken"
        mode_name = mode_name_broken
        supported_platforms = (PlatformType.ANY,)

        def enter_mode(self) -> None:
            raise RuntimeError("foo")

    return BrokenMethod


@pytest.mark.parametrize(
    "args",
    [
        ["-r"],
        ["--keep-running"],
        # Also no args means keep running
        [],
    ],
)
def test_get_argparser_keep_running(args):
    assert parse_arguments(args) == (ModeName.KEEP_RUNNING, [])


@pytest.mark.parametrize(
    "args",
    [
        ["-p"],
        ["--keep-presenting"],
    ],
)
def test_get_argparser_keep_presenting(args):
    assert parse_arguments(args) == (ModeName.KEEP_PRESENTING, [])


@pytest.mark.parametrize(
    "args",
    [
        ["-r", "-p"],
        ["--keep-presenting", "-r"],
        ["-p", "--keep-running"],
        ["--keep-presenting", "--keep-running"],
    ],
)
def test_get_argparser_too_many_modes(args):
    with pytest.raises(ValueError, match="You may only select one of the modes!"):
        assert parse_arguments(args)


@pytest.mark.parametrize(
    "args, expected_mode",
    [
        (["--presentation"], ModeName.KEEP_PRESENTING),
        (["-k"], ModeName.KEEP_RUNNING),
    ],
)
def test_deprecations(args, expected_mode):
    mode, deprecations = parse_arguments(args)
    assert mode == expected_mode
    assert len(deprecations) == 1
    assert f"Using {args[0]} is deprecated in wakepy 0.10.0" in deprecations[0]


def test_get_startup_text_smoke_test():
    assert isinstance(get_startup_text(ModeName.KEEP_PRESENTING), str)


def test_wait_until_keyboardinterrupt():
    def raise_keyboardinterrupt(_):
        raise KeyboardInterrupt

    with patch("wakepy.__main__.time") as timemock:
        timemock.sleep.side_effect = raise_keyboardinterrupt

        wait_until_keyboardinterrupt()


@patch("builtins.print")
def test_handle_activation_error(print_mock):
    result = ActivationResult()
    handle_activation_error(result)
    if sys.version_info[:2] == (3, 7):
        # on python 3.7, need to do other way.
        printed_text = print_mock.mock_calls[0][1][0]
    else:
        printed_text = "\n".join(print_mock.mock_calls[0].args)
    # Some sensible text was printed to the user
    assert "Wakepy could not activate" in printed_text


@patch("wakepy.__main__.wait_until_keyboardinterrupt")
@patch("wakepy.__main__.parse_arguments")
class TestMain:
    """Tests the main() function from the __main__.py in a simple way. This
    is more of a smoke test. The functionality of the different parts is
    already tested in other unit tests."""

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
            call.print(get_startup_text(method1.mode_name)),
            call.wait_until_keyboardinterrupt(),
            call.print("\n\nExited."),
        ]

    @pytest.mark.usefixtures("method2_broken")
    def test_non_working_mode(
        self,
        parse_arguments,
        wait_until_keyboardinterrupt,
        method2_broken,
        monkeypatch,
    ):
        # need to turn off WAKEPY_FAKE_SUCCESS as we want to get a failure.
        monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "0")

        with patch("sys.argv", self.sys_argv), patch("builtins.print") as print_mock:
            manager = self.setup_mock_manager(
                method2_broken,
                print_mock,
                parse_arguments,
                wait_until_keyboardinterrupt,
            )
            main()

        expected_result = ActivationResult(
            results=[], mode_name=method2_broken.mode_name
        )
        assert manager.mock_calls == [
            call.print(get_startup_text(method2_broken.mode_name)),
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
        # resolves to `method.mode_name`
        parse_arguments.return_value = method.mode_name, []

        mocks = Mock()
        mocks.attach_mock(print_mock, "print")
        mocks.attach_mock(wait_until_keyboardinterrupt, "wait_until_keyboardinterrupt")
        return mocks

    @property
    def sys_argv(self):
        # The patched value for sys.argv. Does not matter here otherwise, but
        # should be a list of at least two items.
        return ["", ""]


class TestGetSpinnerSymbols:
    @patch("wakepy.__main__.CURRENT_PLATFORM", IdentifiedPlatformType.LINUX)
    def test_on_linux(self):
        assert get_spinner_symbols() == ["⢎⡰", "⢎⡡", "⢎⡑", "⢎⠱", "⠎⡱", "⢊⡱", "⢌⡱", "⢆⡱"]

    @patch("wakepy.__main__.CURRENT_PLATFORM", IdentifiedPlatformType.WINDOWS)
    @patch("wakepy.__main__.platform.python_implementation", lambda: "PyPy")
    def test_on_windows_pypy(self):
        assert get_spinner_symbols() == ["|", "/", "-", "\\"]
