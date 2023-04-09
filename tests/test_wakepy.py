import pytest

from wakepy import set_keepawake, unset_keepawake, keepawake


def test_run_keepawake():
    set_keepawake()
    unset_keepawake()
