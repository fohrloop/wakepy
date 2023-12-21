from __future__ import annotations

import enum
import itertools
from typing import Type, Iterable

from wakepy.core import CURRENT_PLATFORM
from wakepy.core.method import Method


class MethodIs(enum.IntEnum):
    MISSING = 0  # not implemented
    SUCCESSFUL = 1  # Returns True
    FAILING = 2  # Returns False
    FAILING_MESSAGE = 3  # Return a string (counts as fail)
    RAISING_EXCEPTION = 4


def create_test_method_classes():
    """Helper function for get_test_method_class. (See docs there)
    This basically creates a bunch of Method classes with the
    Method.enter_mode, Method.heartbeat and Method.exit_mode defined
    differently. We do this to make it easier to test every combination
    possible. (5*5*5 = 125 combinations, if number of options in MethodIs is 5)
    """
    test_method_classes = dict()

    class TestException(Exception):
        ...

    # When enter_mode(), heartbear() or exit_mode() returns True, it is
    # considered as being successful
    def successful(self):
        return True

    # When enter_mode(), heartbear() or exit_mode() returns False or a string,
    # it is considered as failing
    def failing(self):
        return False

    def failing_message(self):
        return "failure_reason"

    # The enter_mode(), heartbeat() or exit_mode() *might* raise an exception,
    # like any other method or function ever made. Althought, if there's an
    # exception, it means the implementation has a bug.
    def raising_exception(self):
        raise TestException("foo")

    for enter_mode, heartbeat, exit_mode in itertools.product(MethodIs, repeat=3):
        clsname = f"M{enter_mode.value}{heartbeat.value}{exit_mode.value}"
        clskwargs = {"supported_platforms": CURRENT_PLATFORM, "name": clsname}
        for mode, name in zip(
            (enter_mode, heartbeat, exit_mode), ("enter_mode", "heartbeat", "exit_mode")
        ):
            if mode == MethodIs.SUCCESSFUL:
                clskwargs[name] = successful
            elif mode == MethodIs.FAILING:
                clskwargs[name] = failing
            elif mode == MethodIs.FAILING_MESSAGE:
                clskwargs[name] = failing_message
            elif mode == MethodIs.RAISING_EXCEPTION:
                clskwargs[name] = raising_exception
            else:
                assert mode == MethodIs.MISSING

        test_method_classes[clsname] = type(clsname, (Method,), clskwargs)

    return test_method_classes


_test_method_classes = create_test_method_classes()


def get_test_method_class(
    enter_mode: MethodIs = MethodIs.MISSING,
    heartbeat: MethodIs = MethodIs.MISSING,
    exit_mode: MethodIs = MethodIs.MISSING,
) -> Type[Method]:
    """Get a test Method class with the .enter_mode(), .heartbeat() and
    .exit_mode() methods as wanted.

    MISSING: missing method
    SUCCESSFUL: return True
    FAILING: return False
    FAILING_MESSAGE: return "failure_reason" (string, counted as fail)
    RAISING_EXCEPTION: raises TestException("foo")

    For the expected outcome of each of these, see:
        tests/unit/test_core/test_activation.py
    """
    return _test_method_classes[
        f"M{enter_mode.value}{heartbeat.value}{exit_mode.value}"
    ]


def iterate_test_methods(
    enter_mode=Iterable[MethodIs],
    heartbeat=Iterable[MethodIs],
    exit_mode=Iterable[MethodIs],
) -> Iterable[Method]:
    for enter_mode_, heartbeat_, exit_mode_ in itertools.product(
        enter_mode, heartbeat, exit_mode
    ):
        yield get_test_method_class(
            enter_mode=enter_mode_, heartbeat=heartbeat_, exit_mode=exit_mode_
        )()
