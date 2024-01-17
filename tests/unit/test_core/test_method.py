import re

import pytest

from wakepy.core.method import Method, select_methods
from wakepy.core.registry import MethodRegistryError, get_method, get_methods


def test_overridden_methods_autodiscovery():
    """The enter_mode, heartbeat and exit_mode methods by default do nothing
    (on the Method base class). In subclasses, these are usually overriden.
    Check that detecting the overridden methods works correctly
    """

    class WithEnterAndExit(Method):
        def enter_mode(self):
            return

        def exit_mode(self):
            return

    method1 = WithEnterAndExit()

    assert method1.has_enter
    assert method1.has_exit
    assert not method1.has_heartbeat

    class WithJustHeartBeat(Method):
        def heartbeat(self):
            return

    method2 = WithJustHeartBeat()

    assert not method2.has_enter
    assert not method2.has_exit
    assert method2.has_heartbeat

    class WithEnterExitAndHeartBeat(Method):
        def heartbeat(self):
            return

        def enter_mode(self):
            return

        def exit_mode(self):
            return

    method3 = WithEnterExitAndHeartBeat()

    assert method3.has_enter
    assert method3.has_exit
    assert method3.has_heartbeat

    class SubWithEnterAndHeart(WithJustHeartBeat):
        def enter_mode():
            return

    method4 = SubWithEnterAndHeart()
    assert method4.has_enter
    assert method4.has_heartbeat
    assert not method4.has_exit

    class SubWithEnterAndExit(WithEnterAndExit):
        def enter_mode():
            return 123

    method5 = SubWithEnterAndExit()
    assert method5.has_enter
    assert method5.has_exit
    assert not method5.has_heartbeat


def test_method_has_x_is_not_writeable():
    class MethodWithEnter(Method):
        def enter_mode(self):
            return

    method = MethodWithEnter()
    assert method.has_enter
    assert not method.has_exit

    # The .has_enter, .has_exit or .has_heartbeat should be strictly read-only
    with pytest.raises(AttributeError):
        method.has_enter = False

    with pytest.raises(AttributeError):
        method.has_exit = True

    # Same holds for classes
    with pytest.raises(AttributeError):
        MethodWithEnter.has_enter = False


@pytest.mark.usefixtures("empty_method_registry")
def test_not_possible_to_define_two_methods_with_same_name(testutils, monkeypatch):
    somename = "Some name"

    class SomeMethod(Method):
        name = somename

    # It is not possible to define two methods if same name
    with pytest.raises(
        MethodRegistryError, match=re.escape('Duplicate Method name "Some name"')
    ):

        class SomeMethod(Method):  # noqa:F811
            name = somename

    testutils.empty_method_registry(monkeypatch)

    # Now as the registry is empty it is possible to define method with
    # the same name again
    class SomeMethod(Method):  # noqa:F811
        name = somename


@pytest.mark.usefixtures("provide_methods_a_f")
def test_select_methods():
    (MethodB, MethodD, MethodE) = get_methods(["B", "D", "E"])

    methods = [MethodB, MethodD, MethodE]

    # These can also be filtered with a blacklist
    assert select_methods(methods, omit=["B"]) == [MethodD, MethodE]
    assert select_methods(methods, omit=["B", "E"]) == [MethodD]
    # Extra 'omit' methods do not matter
    assert select_methods(methods, omit=["B", "E", "foo", "bar"]) == [
        MethodD,
    ]

    # These can be filtered with a whitelist
    assert select_methods(methods, use_only=["B", "E"]) == [MethodB, MethodE]

    # If a whitelist contains extra methods, raise exception
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Methods ['bar', 'foo'] in `use_only` are not part of `methods`!"
        ),
    ):
        select_methods(methods, use_only=["foo", "bar"])

    # Cannot provide both: omit and use_only
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Can only define omit (blacklist) or use_only (whitelist), not both!"
        ),
    ):
        select_methods(methods, use_only=["B"], omit=["E"])


def test_method_defaults():
    """tests the Method enter_mode, exit_mode and heartbeat defaults"""
    m = Method()
    assert m.enter_mode() is None
    assert m.heartbeat() is None
    assert m.exit_mode() is None


@pytest.mark.usefixtures("provide_methods_a_f")
def test_method_string_representations():
    MethodB = get_method("B")
    method = MethodB()
    assert method.__str__() == "<wakepy Method: MethodB>"
    assert method.__repr__() == f"<wakepy Method: MethodB at {hex(id(method))}>"
