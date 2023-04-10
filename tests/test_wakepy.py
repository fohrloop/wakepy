"""This module contains the system-independent tests and
tests which are identical on all systems.

For system-dependent tests, see test_on_{system}.py
"""

import pytest

from wakepy import keepawake, set_keepawake, unset_keepawake


def test_run_set_keepawake_unset_keepawake():
    set_keepawake()
    unset_keepawake()


def test_run_keepawake():
    # Test the context manager syntax
    with keepawake():
        ...

    # Test that errors occured inside context manager are not suppressed
    with pytest.raises(ZeroDivisionError):
        with keepawake():
            1 / 0
