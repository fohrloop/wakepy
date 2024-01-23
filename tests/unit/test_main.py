"""Tests for the __main__ CLI"""
from unittest.mock import patch

import pytest

from wakepy.__main__ import (
    get_startup_text,
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
