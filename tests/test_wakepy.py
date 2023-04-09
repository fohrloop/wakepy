import pytest


def test_run_keepawake():
    from wakepy import set_keepawake, unset_keepawake, keepawake

    set_keepawake()
    unset_keepawake()


def test_get_module_names():
    from wakepy.keepawake import get_module_names

    raise NotImplementedError()
