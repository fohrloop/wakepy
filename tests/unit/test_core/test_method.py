import re

import pytest

from wakepy.core.method import (
    Method,
    MethodDefinitionError,
    get_method,
    get_methods,
    get_methods_for_mode,
    method_names_to_classes,
    select_methods,
    register_method,
)


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


def test_get_method_which_is_not_yet_defined(monkeypatch):
    monkeypatch.setattr("wakepy.core.method._method_registry", dict())

    # The method registry is empty so there is no Methods with the name
    with pytest.raises(
        KeyError, match=re.escape('No Method with name "Some name" found!')
    ):
        get_method("Some name")


def test_get_method_working_example(monkeypatch):
    somename = "Some name"
    # Make the registry empty
    monkeypatch.setattr("wakepy.core.method._method_registry", dict())

    # Create a method
    class SomeMethod(Method):
        name = somename

    # Check that we can retrieve the method
    method_class = get_method(somename)
    assert method_class is SomeMethod


def test_not_possible_to_define_two_methods_with_same_name(monkeypatch):
    somename = "Some name"
    # Make the registry empty
    monkeypatch.setattr("wakepy.core.method._method_registry", dict())

    class SomeMethod(Method):
        name = somename

    # It is not possible to define two methods if same name
    with pytest.raises(
        MethodDefinitionError, match=re.escape('Duplicate Method name "Some name"')
    ):

        class SomeMethod(Method):  # noqa:F811
            name = somename

    # sanity check: The monkeypatching works as we expect
    monkeypatch.setattr("wakepy.core.method._method_registry", dict())

    # Now as the registry is empty it is possible to define method with
    # the same name again
    class SomeMethod(Method):  # noqa:F811
        name = somename


@pytest.mark.usefixtures("provide_methods_a_f")
def test_method_names_to_classes():
    (A, B, C) = get_methods(["A", "B", "C"])

    # Asking for a list, getting a list
    assert method_names_to_classes(["A", "B"]) == [A, B]
    # The order of returned items matches the order of input params
    assert method_names_to_classes(["C", "B", "A"]) == [C, B, A]
    assert method_names_to_classes(["B", "A", "C"]) == [B, A, C]

    # Asking a tuple, getting a tuple
    assert method_names_to_classes(("A", "B")) == (A, B)
    assert method_names_to_classes(("C", "B", "A")) == (C, B, A)

    # Asking a set, getting a set
    assert method_names_to_classes({"A", "B"}) == {A, B}
    assert method_names_to_classes({"C", "B"}) == {C, B}

    # Asking None, getting None
    assert method_names_to_classes(None) is None

    # Asking something that does not exists will raise KeyError
    with pytest.raises(KeyError, match=re.escape('No Method with name "foo" found!')):
        method_names_to_classes(["A", "foo"])

    # Using unsupported type raises TypeError
    with pytest.raises(TypeError):
        method_names_to_classes(4123)


@pytest.mark.usefixtures("provide_methods_a_f")
def test_get_methods_for_mode():
    methods = get_methods(["A", "B", "C", "D", "E", "F"])
    (MethodA, MethodB, _, MethodD, MethodE, MethodF) = methods

    assert get_methods_for_mode("first_mode") == [
        MethodB,
        MethodD,
        MethodE,
    ]
    assert get_methods_for_mode("second_mode") == [
        MethodA,
        MethodF,
    ]


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


def test_register_method(monkeypatch):
    # Make the registry empty
    monkeypatch.setattr("wakepy.core.method._method_registry", dict())

    class MethodA(Method):
        name = "A"

    assert get_method("A") is MethodA

    # It is possible to register the same method many times without issues.
    register_method(MethodA)
    register_method(MethodA)
    register_method(MethodA)

    assert get_method("A") is MethodA
