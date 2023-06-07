"""Test the deprecated part of wakepy

Deprecated in 0.7.0"""


import platform

from wakepy import keepawake, set_keepawake, unset_keepawake

CURRENT_SYSTEM = platform.system().lower()


def test_smoke_test():
    """simple smoke test"""

    set_keepawake(keep_screen_awake=False)
    unset_keepawake()

    with keepawake(keep_screen_awake=False):
        pass
