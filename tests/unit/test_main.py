"""Unit tests for the __main__ module"""

import sys
from unittest.mock import patch

import pytest

from wakepy import ActivationResult, Method, Mode
from wakepy.__main__ import (
    _get_success_or_fail_symbol,
    get_should_use_ascii_only,
    get_spinner_symbols,
    get_wakepy_cli_info,
    handle_activation_error,
    main,
    parse_arguments,
    wait_until_keyboardinterrupt,
)
from wakepy.core import PlatformType
from wakepy.core.constants import IdentifiedPlatformType, ModeName
from wakepy.methods._testing import WakepyFakeSuccess


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
    assert parse_arguments(args) == (ModeName.KEEP_RUNNING, "")


@pytest.mark.parametrize(
    "args",
    [
        ["-p"],
        ["--keep-presenting"],
    ],
)
def test_get_argparser_keep_presenting(args):
    assert parse_arguments(args) == (ModeName.KEEP_PRESENTING, "")


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
    assert f"Using {args[0]} is deprecated in wakepy 0.10.0" in deprecations


def test_wait_until_keyboardinterrupt():
    def raise_keyboardinterrupt(_):
        raise KeyboardInterrupt

    with patch("wakepy.__main__.time") as timemock:
        timemock.sleep.side_effect = raise_keyboardinterrupt

        wait_until_keyboardinterrupt(True)


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


@patch("wakepy.__main__.parse_arguments")
class TestMain:
    """Tests the main() function from the __main__.py in a simple way. This
    is more of a smoke test. The functionality of the different parts is
    already tested in other unit tests."""

    def test_working_mode(
        self,
        parse_arguments,
        method1,
    ):

        with patch("wakepy.__main__.wait_until_keyboardinterrupt"), patch(
            "sys.argv", self.sys_argv
        ), patch("builtins.print"):
            self.setup_mocks(method1, parse_arguments)
            main()

    @pytest.mark.usefixtures("method2_broken")
    def test_non_working_mode(
        self,
        parse_arguments,
        method2_broken,
        monkeypatch,
    ):
        # need to turn off WAKEPY_FAKE_SUCCESS as we want to get a failure.
        monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "0")

        with patch("wakepy.__main__.wait_until_keyboardinterrupt"), patch(
            "sys.argv", self.sys_argv
        ), patch("builtins.print"):
            self.setup_mocks(method2_broken, parse_arguments)
            main()

    @staticmethod
    def setup_mocks(
        method: Method,
        parse_arguments,
    ):
        # Assume that user has specified some mode in the commandline which
        # resolves to `method.mode_name`
        parse_arguments.return_value = method.mode_name, []

    @property
    def sys_argv(self):
        # The patched value for sys.argv. Does not matter here otherwise, but
        # should be a list of at least two items.
        return ["", ""]


# fmt: off
class TestGetSpinnerSymbols:
    def test_non_ascii(self):
        assert get_spinner_symbols(False) == ["⢎⡰", "⢎⡡", "⢎⡑", "⢎⠱", "⠎⡱", "⢊⡱", "⢌⡱", "⢆⡱"] # noqa: E501

    def test_ascii(self):
        assert get_spinner_symbols(True) == ["|", "/", "-", "\\"]
# fmt: on


class TestShouldUseAsciiOnly:
    @patch("wakepy.__main__.CURRENT_PLATFORM", IdentifiedPlatformType.LINUX)
    def test_on_linux(self):
        assert get_should_use_ascii_only() is False

    @patch("wakepy.__main__.CURRENT_PLATFORM", IdentifiedPlatformType.WINDOWS)
    @patch("wakepy.__main__.platform.python_implementation", lambda: "PyPy")
    def test_on_windows_pypy(self):
        assert get_should_use_ascii_only() is True


@pytest.fixture
def somemode():
    return Mode([WakepyFakeSuccess], name="testmode")


class TestGetWakepyCliInfo:

    @patch("wakepy.__version__", "0.10.0")
    def test_get_wakepy_cli_info(self, somemode: Mode):

        deprecations = "This thing is deprecated"

        with somemode as m:
            info = get_wakepy_cli_info(
                m,
                ascii_only=False,
                deprecations="",
            )
        assert "v.0.10.0" in info
        assert "[✔] Programs keep running" in info
        assert "[ ] Display kept on, screenlock disabled" in info
        assert "Method: WAKEPY_FAKE_SUCCESS" in info
        assert deprecations not in info

        with somemode as m:
            info = get_wakepy_cli_info(
                m,
                ascii_only=False,
                deprecations=deprecations,
            )
        assert deprecations in info


class TestGetSuccessOrFailSymbol:
    @pytest.mark.parametrize(
        "success, ascii_only, expected",
        [
            (True, True, "x"),
            (False, True, " "),
            (True, False, "✔"),
            (False, False, " "),
        ],
    )
    def test_get_success_or_fail_symbol(self, success, ascii_only, expected):
        assert _get_success_or_fail_symbol(success, ascii_only) == expected
