import enum
import itertools

from wakepy.core.configuration import CURRENT_SYSTEM
from wakepy.core.method import Method


class MethodIs(enum.IntEnum):
    MISSING = 0
    SUCCESSFUL = 1
    RAISING_EXCEPTION = 2


def create_test_method_classes():
    """Helper function for get_test_method_class. (See docs there)"""
    test_method_classes = dict()

    class TestException(Exception):
        ...

    def successful(self):
        ...

    def raising_exception(self):
        raise TestException("foo")

    for enter_mode, heartbeat, exit_mode in itertools.product(MethodIs, repeat=3):
        clsname = f"M{enter_mode.value}{heartbeat.value}{exit_mode.value}"
        clskwargs = {"supported_systems": CURRENT_SYSTEM, "name": clsname}
        for mode, name in zip(
            (enter_mode, heartbeat, exit_mode), ("enter_mode", "heartbeat", "exit_mode")
        ):
            if mode == MethodIs.SUCCESSFUL:
                clskwargs[name] = successful
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
):
    """Get a test Method class with the .enter_mode(), .heartbeat() and
    .exit_mode() methods as wanted.

    Each of the methods is either
    0: not implemented (missing method)
    1: successful (implemented and not raising exception)
    2: exception (implemented and raising exception)

    For the expected outcome of each of these, see:
        tests/unit/test_core/test_method.py
    """
    return _test_method_classes[
        f"M{enter_mode.value}{heartbeat.value}{exit_mode.value}"
    ]
