"""Tests for the __main__ CLI"""
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from wakepy import ModeExit
from wakepy.__main__ import (
    get_startup_text,
    main,
    parse_arguments,
    handle_activation_error,
    wait_until_keyboardinterrupt,
)
from wakepy.core import Mode
from wakepy.core.constants import ModeName


@pytest.mark.parametrize(
    "args",
    [
        ["-k"],
        ["--keep-running"],
        # Also no args means keep running
        [],
    ],
)
def test_get_argparser_keep_running(args):
    assert parse_arguments(args) == ModeName.KEEP_RUNNING


@pytest.mark.parametrize(
    "args",
    [
        ["-p"],
        ["--presentation"],
    ],
)
def test_get_argparser_keep_presenting(args):
    assert parse_arguments(args) == ModeName.KEEP_PRESENTING


@pytest.mark.parametrize(
    "args",
    [
        ["-k", "-p"],
        ["--presentation", "-k"],
        ["-p", "--keep-running"],
        ["--presentation", "--keep-running"],
    ],
)
def test_get_argparser_too_many_modes(args):
    with pytest.raises(ValueError, match="You may only select one of the modes!"):
        assert parse_arguments(args)


def test_get_startup_text_smoke_test():
    assert isinstance(get_startup_text(ModeName.KEEP_PRESENTING), str)


def test_wait_until_keyboardinterrupt():
    def raise_keyboardinterrupt(_):
        raise KeyboardInterrupt

    with patch("wakepy.__main__.time") as timemock:
        timemock.sleep.side_effect = raise_keyboardinterrupt

        wait_until_keyboardinterrupt()


def get_mocks_for_main(
    parse_arguments,
    create_mode,
    get_startup_text,
    wait_until_keyboardinterrupt,
    mode_works: bool,
):
    cli_arg = Mock()
    mockmodename = Mock(spec_set=ModeName.KEEP_PRESENTING)
    mockprint = Mock()

    class TestMode(Mode):
        active = mode_works

    mockmode = MagicMock(spec_set=TestMode)
    mockmode.active = mode_works
    sysarg = ["programname", cli_arg]
    parse_arguments.return_value = mockmodename
    get_startup_text.return_value = "startuptext"
    create_mode.return_value = mockmode

    mocks = Mock()
    mocks.sysarg = sysarg
    mocks.attach_mock(mockprint, "print")
    mocks.attach_mock(mockmode, "mode")
    mocks.attach_mock(parse_arguments, "parse_arguments")
    mocks.attach_mock(create_mode, "create_mode")
    mocks.attach_mock(get_startup_text, "get_startup_text")
    mocks.attach_mock(wait_until_keyboardinterrupt, "wait_until_keyboardinterrupt")
    return mocks


@patch("wakepy.__main__.wait_until_keyboardinterrupt")
@patch("wakepy.__main__.get_startup_text")
@patch("wakepy.__main__.create_mode")
@patch("wakepy.__main__.parse_arguments")
def test_main(
    parse_arguments, create_mode, get_startup_text, wait_until_keyboardinterrupt
):
    """This is just a smoke test for the main() function. It checks that
    correct functions are called in the correct order and correct arguments,
    but the functionality of each of the functions is tested elsewhere."""

    mocks = get_mocks_for_main(
        parse_arguments,
        create_mode,
        get_startup_text,
        wait_until_keyboardinterrupt,
        mode_works=True,
    )

    with patch("sys.argv", mocks.sysarg), patch("builtins.print", mocks.print):
        main()

    assert mocks.mock_calls == [
        call.parse_arguments(mocks.sysarg[1:]),
        call.create_mode(modename=parse_arguments.return_value),
        call.print("startuptext"),
        call.mode.__enter__(),
        call.get_startup_text(mode=parse_arguments.return_value),
        call.print(get_startup_text.return_value),
        call.wait_until_keyboardinterrupt(),
        call.mode.__exit__(None, None, None),
        call.print("\nExited."),
    ]


@patch("wakepy.__main__.wait_until_keyboardinterrupt")
@patch("wakepy.__main__.get_startup_text")
@patch("wakepy.__main__.create_mode")
@patch("wakepy.__main__.parse_arguments")
def test_main_with_non_working_mode(
    parse_arguments, create_mode, get_startup_text, wait_until_keyboardinterrupt
):
    mocks = get_mocks_for_main(
        parse_arguments,
        create_mode,
        get_startup_text,
        wait_until_keyboardinterrupt,
        mode_works=False,
    )

    with patch("sys.argv", mocks.sysarg), patch("builtins.print", mocks.print):
        with pytest.raises(ModeExit):
            main()
    assert mocks.mock_calls == [
        call.parse_arguments(mocks.sysarg[1:]),
        call.create_mode(
            modename=parse_arguments.return_value, on_fail=handle_activation_error
        ),
        call.get_startup_text(mode=parse_arguments.return_value),
        call.print(get_startup_text.return_value),
        call.mode.__enter__(),
        # Checking only the exception type here. The exception and the trackeback
        # instances are assumed to be correct. Too complicated to catch them
        # just for the test.
        call.mode.__exit__(ModeExit, *mocks.mock_calls[-1].args[1:]),
    ]
