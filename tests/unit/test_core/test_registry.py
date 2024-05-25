import re

import pytest

from tests.unit.test_core.testmethods import TestMethod
from wakepy.core import Method, get_method, get_methods, get_methods_for_mode
from wakepy.core.registry import register_method


@pytest.mark.usefixtures("empty_method_registry")
def test_get_method_which_is_not_yet_defined():
    # The method registry is empty so there is no Methods with the name
    with pytest.raises(
        ValueError, match=re.escape('No Method with name "Some name" found!')
    ):
        get_method("Some name")
    with pytest.raises(
        ValueError, match=re.escape('No Method with name "Some name" found!')
    ):
        # for test coverage, test this branch, too.
        get_method("Some name", mode_name="foo")


@pytest.mark.usefixtures("empty_method_registry")
def test_get_method_working_example():
    somename = "Some name"

    # Create a method
    class SomeMethod(TestMethod):
        name = somename

    # Check that we can retrieve the method
    method_class = get_method(somename)
    assert method_class is SomeMethod


def test_get_methods(testutils, monkeypatch):
    testutils.empty_method_registry(monkeypatch)

    class A(TestMethod):
        name = "A"

    class B(TestMethod):
        name = "B"

    class C(TestMethod):
        name = "C"

    # Asking for a list, getting a list
    assert get_methods(["A", "B"]) == [A, B]
    # The order of returned items matches the order of input params
    assert get_methods(["C", "B", "A"]) == [C, B, A]
    assert get_methods(["B", "A", "C"]) == [B, A, C]

    # Asking a tuple, getting a tuple
    assert get_methods(("A", "B")) == (A, B)
    assert get_methods(("C", "B", "A")) == (C, B, A)

    # Asking a set, getting a set
    assert get_methods({"A", "B"}) == {A, B}
    assert get_methods({"C", "B"}) == {C, B}

    # Asking something that does not exists will raise KeyError
    with pytest.raises(ValueError, match=re.escape('No Method with name "foo" found!')):
        get_methods(["A", "foo"])

    # Using unsupported type raises TypeError
    with pytest.raises(TypeError):
        get_methods(4123)  # type: ignore

    with pytest.raises(TypeError):
        get_methods(None)  # type: ignore


@pytest.mark.usefixtures("provide_methods_a_f")
def test_get_methods_for_mode():
    MethodA, MethodB, MethodD, MethodE, MethodF = get_methods(["A", "B", "D", "E", "F"])

    assert get_methods_for_mode("first_mode") == [
        MethodB,
        MethodD,
        MethodE,
    ]
    assert get_methods_for_mode("second_mode") == [
        MethodA,
        MethodF,
    ]


@pytest.mark.usefixtures("empty_method_registry")
def test_register_method():
    # Note that defining a subclass automatically registers a method.
    class MethodA(Method):
        name = "A"
        mode_name = "foo"

    assert get_method("A") is MethodA

    # It is possible to register the same method many times without issues.
    register_method(MethodA)
    register_method(MethodA)

    assert get_method("A") is MethodA

    class MethodA2(Method):
        name = "A"
        mode_name = "somemode"

    #  We can get both of the methods from the register
    assert get_method("A", mode_name="foo") is MethodA
    assert get_method("A", mode_name="somemode") is MethodA2

    # We can get the method from register after registering it.
    class MethodA3(Method):
        name = "A"
        mode_name = "yet_another_mode"

    assert get_method("A", mode_name="foo") is MethodA
    assert get_method("A", mode_name="somemode") is MethodA2
    assert get_method("A", mode_name="yet_another_mode") is MethodA3

    ## We get ValueError if trying to get a method by name when there are
    # multiple alternatives (unambiguity)
    with pytest.raises(
        ValueError,
        match=re.escape(
            """Multiple (3) Methods with name "A" found! The selection is """
            """unambiguous. Found modes: ('foo', 'somemode', 'yet_another_mode')"""
        ),
    ):
        get_method("A")
