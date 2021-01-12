"""This module provides 

start() 
- Function that starts a "keepawake". Keeps the computer
  awake. Exit with Ctrl-C.

set_keepawake()
unset_keepawake()
- The lower level functions that can be used in any script to
   set or unset the keepawake.
"""
from functools import wraps
import platform
import time


SYSTEM = platform.system().lower()


if SYSTEM == "windows":
    from ._win import set_keepawake, unset_keepawake
else:
    NotImplementedError(
        f"wakepy has not yet a {SYSTEM} implementation. Pull requests welcome: https://github.com/np-8/wakepy"
    )

p = ["|", "/", "-", "\\"]


def wait_until_keyboardinterrupt():
    try:
        print(
            "Started wakepy. Your computer will not sleep automatically (unless battery goes under critical level)"
        )
        while True:
            for i in range(0, 4):
                print("\r" + p[i] + r" [Press Ctrl+C to exit]", end="")
                time.sleep(1)
    except KeyboardInterrupt:
        pass


def start():
    set_keepawake()
    wait_until_keyboardinterrupt()
    unset_keepawake()
