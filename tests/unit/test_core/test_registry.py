import re

import pytest

from wakepy.core import Method
from wakepy.core.registry import (
    get_method,
    get_methods,
    get_methods_for_mode,
    method_names_to_classes,
    register_method,
)


@pytest.mark.usefixtures("empty_method_registry")
def test_get_method_which_is_not_yet_defined(monkeypatch):
    # The method registry is empty so there is no Methods with the name
    with pytest.raises(
        KeyError, match=re.escape('No Method with name "Some name" found!')
    ):
        get_method("Some name")


@pytest.mark.usefixtures("empty_method_registry")
def test_get_method_working_example(monkeypatch):
    somename = "Some name"

    # Create a method
    class SomeMethod(Method):
        name = somename

    # Check that we can retrieve the method
    method_class = get_method(somename)
    assert method_class is SomeMethod


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


@pytest.mark.usefixtures("empty_method_registry")
def test_register_method(monkeypatch):
    class MethodA(Method):
        name = "A"

    assert get_method("A") is MethodA

    # It is possible to register the same method many times without issues.
    register_method(MethodA)
    register_method(MethodA)
    register_method(MethodA)

    assert get_method("A") is MethodA
