"""Unit tests for the __main__ module"""

import sys
from unittest.mock import patch

import pytest

from wakepy import ActivationResult
from wakepy.__main__ import (
    get_startup_text,
    handle_activation_error,
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
