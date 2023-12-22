from __future__ import annotations

import itertools
from typing import Iterable, Type

from wakepy.core import CURRENT_PLATFORM
from wakepy.core.method import Method


class WakepyMethodTestError(Exception):
    ...


def get_new_classname(prefix="TestMethod") -> str:
    """Creates a new class name. Just to make it easier to generate lots of
    Methods."""
    if not hasattr(get_new_classname, "counter"):
        get_new_classname.counter = 0
    get_new_classname.counter += 1
    return f"{prefix}{get_new_classname.counter}"


_test_method_classes = dict()
"""Container for all created method classes (caching for get_test_method_class)"""
METHOD_MISSING = "__method_is_not_implemented__"
"""Magic constant for creating classes with some functions not implemented"""
FAILURE_REASON = "failure_reason"
DEFAULT_ERROR_TEXT = "wakepy test error"
METHOD_OPTIONS = [
    METHOD_MISSING,
    True,
    False,
    FAILURE_REASON,
    WakepyMethodTestError(DEFAULT_ERROR_TEXT),
]


def get_test_method_class(
    *,
    caniuse=METHOD_MISSING,
    enter_mode=METHOD_MISSING,
    heartbeat=METHOD_MISSING,
    exit_mode=METHOD_MISSING,
) -> Type[Method]:
    """Get a test Method class with the .caniuse(), .enter_mode(), .heartbeat()
    and .exit_mode() methods defined as wanted. All methods can either be:

    (a) METHOD_MISSING: missing method. The created Method subclass will have
        the default implementation from the Method class.
    (b) An instance of an Exception. For example MyException('foo'). In this
        case, the exception will be raised.
    (c) Any value. In this case, the value will be returned. Typical values
      are True (success), string (fail with a reason), False (fail without
      giving a reason) and None.

    For the expected outcome of each of these, see:
        tests/unit/test_core/test_activation.py
    """

    def _create_function(instructions):
        if instructions == METHOD_MISSING:
            return None
        elif isinstance(instructions, type) and issubclass(instructions, BaseException):

            def m(self):
                raise instructions()

        elif isinstance(instructions, Exception):

            def m(self):
                raise instructions

        else:
            m = lambda self: instructions
        return m

    def _create_class():
        clsname = get_new_classname()
        clskwargs = {"supported_platforms": CURRENT_PLATFORM, "name": clsname}
        clsmethods = dict()
        clsmethods["caniuse"] = _create_function(caniuse)
        clsmethods["enter_mode"] = _create_function(enter_mode)
        clsmethods["exit_mode"] = _create_function(exit_mode)
        clsmethods["heartbeat"] = _create_function(heartbeat)
        clskwargs = {
            **clskwargs,
            **{k: v for k, v in clsmethods.items() if callable(v)},
        }
        return type(clsname, (Method,), clskwargs)

    key = (enter_mode, heartbeat, exit_mode)
    if key not in _test_method_classes:
        _test_method_classes[key] = _create_class()

    return _test_method_classes[key]


def iterate_test_methods(
    enter_mode=Iterable,
    heartbeat=Iterable,
    exit_mode=Iterable,
) -> Iterable[Method]:
    for enter_mode_, heartbeat_, exit_mode_ in itertools.product(
        enter_mode, heartbeat, exit_mode
    ):
        yield get_test_method_class(
            enter_mode=enter_mode_, heartbeat=heartbeat_, exit_mode=exit_mode_
        )()


# Just test that iterating the test methods works as expected
_methods = list(
    iterate_test_methods(
        enter_mode=[METHOD_MISSING],
        heartbeat=[
            METHOD_MISSING,
            False,
            "Failure reason",
        ],
        exit_mode=METHOD_OPTIONS,
    )
)
assert len(_methods) == 1 * 3 * 5
assert all(isinstance(m, Method) for m in _methods)
del _methods
