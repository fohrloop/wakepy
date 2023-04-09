"""This module provides the following core functions of wakepy:

keepawake()
    A context manager that sets and unsets keepawake.

set_keepawake()
unset_keepawake()
    The lower level functions that can be used in any script to
    set or unset the keepawake.
"""
from ._core import set_keepawake, unset_keepawake, keepawake
