"""Tests for the __main__ CLI"""
from unittest.mock import patch, Mock, call

import pytest

from wakepy.__main__ import (
    get_startup_text,
    main,
    parse_arguments,
    wait_until_keyboardinterrupt,
)
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
    assert parse_arguments(args) == dict(modename=ModeName.KEEP_RUNNING)


@pytest.mark.parametrize(
    "args",
    [
        ["-p"],
        ["--presentation"],
    ],
)
def test_get_argparser_keep_presenting(args):
    assert parse_arguments(args) == dict(modename=ModeName.KEEP_PRESENTING)


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
    cli_arg = Mock()
    mockmodename = Mock(spec_set=ModeName.KEEP_PRESENTING)
    mockprint = Mock()
    sysarg = ["programname", cli_arg]
    parse_arguments.return_value = dict(modename=mockmodename)
    get_startup_text.return_value = "startuptext"

    mocks = Mock()
    mocks.attach_mock(mockprint, "print")
    mocks.attach_mock(parse_arguments, "parse_arguments")
    mocks.attach_mock(create_mode, "create_mode")
    mocks.attach_mock(get_startup_text, "get_startup_text")
    mocks.attach_mock(wait_until_keyboardinterrupt, "wait_until_keyboardinterrupt")

    with patch("sys.argv", sysarg), patch("builtins.print", mockprint):
        main()

    assert mocks.mock_calls == [
        call.parse_arguments([cli_arg]),
        call.create_mode(modename=mockmodename),
        call.create_mode().__enter__(),
        call.create_mode().active.__bool__(),
        call.get_startup_text(mode=mockmodename),
        call.print(get_startup_text.return_value),
        call.wait_until_keyboardinterrupt(),
        call.create_mode().__exit__(None, None, None),
        call.print("\nExited."),
    ]
