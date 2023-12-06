import itertools
import re

import pytest
from testmethods import MethodIs, get_test_method_class

from wakepy.core.method import (
    EnterModeError,
    ExitModeError,
    HeartbeatCallError,
    Method,
    MethodCurationOpts,
    MethodDefinitionError,
    MethodError,
    check_priority_order,
    get_method,
    get_methods,
    get_methods_for_mode,
    method_names_to_classes,
    get_prioritized_methods_groups,
    select_methods,
)


@pytest.fixture(scope="function")
def provide_methods_a_f(monkeypatch):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    class MethodA(Method):
        name = "A"

    class MethodB(Method):
        name = "B"

    class MethodC(Method):
        name = "C"

    class MethodD(Method):
        name = "D"

    class MethodE(Method):
        name = "E"

    class MethodF(Method):
        name = "F"


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
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    # The method registry is empty so there is no Methods with the name
    with pytest.raises(
        KeyError, match=re.escape('No Method with name "Some name" found!')
    ):
        get_method("Some name")


def test_get_method_working_example(monkeypatch):
    somename = "Some name"
    # Make the registry empty
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    # Create a method
    class SomeMethod(Method):
        name = somename

    # Check that we can retrieve the method
    method_class = get_method(somename)
    assert method_class is SomeMethod


def test_not_possible_to_define_two_methods_with_same_name(monkeypatch):
    somename = "Some name"
    # Make the registry empty
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    class SomeMethod(Method):
        name = somename

    # It is not possible to define two methods if same name
    with pytest.raises(
        MethodDefinitionError, match=re.escape('Duplicate Method name "Some name"')
    ):

        class SomeMethod(Method):
            name = somename

    # sanity check: The monkeypatching works as we expect
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    # Now as the registry is empty it is possible to define method with
    # the same name again
    class SomeMethod(Method):
        name = somename


def test_method_names_to_classes(monkeypatch):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    class A(Method):
        name = "A"

    class B(Method):
        name = "B"

    class C(Method):
        name = "C"

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
    with pytest.raises(KeyError, match=re.escape('No Method with name "D" found!')):
        method_names_to_classes(["A", "D"])

    # Using unsupported type raises TypeError
    with pytest.raises(TypeError):
        method_names_to_classes(4123)


def test_all_combinations_with_switch_to_the_mode():
    """Test that each of following combinations:

        {enter_mode} {heartbeat} {exit_mode}

    where each of {enter_mode}, {heartbeat} and {exit_mode} is either
    0: not implemented (missing method)
    1: successful (implemented and not raising exception)
    2: exception (implemented and raising exception)"

    works as expected.
    """

    for enter_mode, heartbeat, exit_mode in itertools.product(
        (MethodIs.MISSING, MethodIs.SUCCESSFUL, MethodIs.RAISING_EXCEPTION),
        (MethodIs.MISSING, MethodIs.SUCCESSFUL, MethodIs.RAISING_EXCEPTION),
        (MethodIs.MISSING, MethodIs.SUCCESSFUL, MethodIs.RAISING_EXCEPTION),
    ):
        method = get_test_method_class(
            enter_mode=enter_mode, heartbeat=heartbeat, exit_mode=exit_mode
        )()

        if enter_mode == heartbeat == MethodIs.MISSING:
            # enter_mode and heartbeat both missing -> not possible to switch
            assert not method.activate_the_mode()
            assert isinstance(method.mode_switch_exception, MethodError)
            continue
        elif MethodIs.RAISING_EXCEPTION not in (enter_mode, heartbeat):
            # When neither enter_mode or heartbeat will cause exception,
            # the switch should be successful
            assert method.activate_the_mode()
            assert method.mode_switch_exception is None
        elif enter_mode == MethodIs.RAISING_EXCEPTION:
            # If enter_mode has exception, switch is not successful
            # .. and the exception type is EnterModeError
            assert not method.activate_the_mode()
            assert isinstance(method.mode_switch_exception, EnterModeError)
        elif (heartbeat == MethodIs.RAISING_EXCEPTION) and (
            exit_mode != MethodIs.RAISING_EXCEPTION
        ):
            # If heartbeat has exception, switch is not successful
            # .. and the exception type is HeartbeatCallError
            assert not method.activate_the_mode()
            assert isinstance(method.mode_switch_exception, HeartbeatCallError)
        elif (heartbeat == MethodIs.RAISING_EXCEPTION) and (
            exit_mode == MethodIs.RAISING_EXCEPTION
        ):
            # If heartbeat has exception, we try to back off by calling
            # exit_mode. If that fails, there should be exception raised.
            with pytest.raises(ExitModeError):
                method.activate_the_mode()
        else:
            # Test case missing? Should not happen ever.
            raise Exception(method.__class__.__name__)


def test_get_methods_for_mode(monkeypatch):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    # B, D, E
    first_mode = "first_mode"
    # A, F
    second_mode = "second_mode"

    # The register is empty at start
    assert get_methods_for_mode(first_mode) == []
    assert get_methods_for_mode(second_mode) == []

    class MethodA(Method):
        name = "A"
        mode = second_mode

    class MethodB(Method):
        name = "B"
        mode = first_mode

    class MethodC(Method):
        name = "C"

    class MethodD(Method):
        name = "D"
        mode = first_mode

    class MethodE(Method):
        name = "E"
        mode = first_mode

    class MethodF(Method):
        name = "F"
        mode = second_mode

    # Now, there are methods
    assert get_methods_for_mode(first_mode) == [
        MethodB,
        MethodD,
        MethodE,
    ]
    assert get_methods_for_mode(second_mode) == [
        MethodA,
        MethodF,
    ]


def test_select_methods(monkeypatch):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    class MethodB(Method):
        name = "B"

    class MethodD(Method):
        name = "D"

    class MethodE(Method):
        name = "E"

    methods = [MethodB, MethodD, MethodE]

    # These can also be filtered with a blacklist
    assert select_methods(methods, skip=["B"]) == [MethodD, MethodE]
    assert select_methods(methods, skip=["B", "E"]) == [MethodD]
    # Extra 'skip' methods do not matter
    assert select_methods(methods, skip=["B", "E", "foo", "bar"]) == [
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


def test_method_curation_opts_constructor(monkeypatch):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    class Foo(Method):
        name = "foo"

    class MethodA(Method):
        name = "A"

    opts = MethodCurationOpts.from_names(skip=["A"], higher_priority=["foo"])
    assert opts.skip == [MethodA]
    assert opts.higher_priority == [Foo]

    # Should not be possible to define both: use_only and skip
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Can only define skip (blacklist) or use_only (whitelist), not both!"
        ),
    ):
        MethodCurationOpts.from_names(skip=["A"], use_only=["foo"])

    # Should not be possible to define same method in lower and higher priority
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Cannot have same methods in higher_priority and lower_priority! (Methods: {A})"
        ),
    ):
        MethodCurationOpts.from_names(higher_priority=["A"], lower_priority=["A"])

    # Cannot skip and prioritize methods
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Cannot have same methods in `skip` and `higher_priority` or `lower_priority`!"
        ),
    ):
        MethodCurationOpts.from_names(higher_priority=["A"], skip=["A"])
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Cannot have same methods in `skip` and `higher_priority` or `lower_priority`!"
        ),
    ):
        MethodCurationOpts.from_names(lower_priority=["A"], skip=["A"])


@pytest.mark.usefixtures("provide_methods_a_f")
def test_check_priority_order():
    methods = get_methods(["A", "B", "C", "D", "E", "F"])
    (MethodA, *_) = methods

    # These should be fine
    check_priority_order(priority_order=None, methods=methods)
    check_priority_order(priority_order=["*"], methods=methods)
    # Simple list of methods
    check_priority_order(priority_order=["A", "B", "F"], methods=methods)
    # Simple list of methods with asterisk
    check_priority_order(priority_order=["A", "B", "*", "F"], methods=methods)
    # Simple set + strings
    check_priority_order(priority_order=[{"A", "B"}, "*", "F"], methods=methods)
    # Simple set + strings
    check_priority_order(priority_order=[{"A", "B"}, "*", "E", {"F"}], methods=methods)

    # These are not fine
    # There is no Method with name "X" in methods
    with pytest.raises(
        ValueError,
        match=re.escape('Method "X" in priority_order not in selected methods!'),
    ):
        check_priority_order(priority_order=["X"], methods=methods)

    # two asterisks
    with pytest.raises(
        ValueError,
        match=re.escape("The asterisk (*) can only occur once in priority_order!"),
    ):
        check_priority_order(priority_order=["A", "*", "B", "*"], methods=methods)

    # Asterisk inside a set
    with pytest.raises(
        ValueError,
        match=re.escape("Asterisk (*) may not be a part of a set in priority_order!"),
    ):
        check_priority_order(priority_order=[{"*"}], methods=methods)

    # Unsupported type
    with pytest.raises(
        TypeError,
        match=re.escape("priority_order must be a list[str | set[str]]!"),
    ):
        check_priority_order(priority_order=[MethodA], methods=methods)


@pytest.mark.usefixtures("provide_methods_a_f")
def test_get_prioritized_methods_groups_does_not_edit_args():
    """Test that the prioriry_order argument is not modified by the function"""
    methods = get_methods(["A", "B", "C", "D", "E", "F"])

    priority_order = ["A", "F"]

    _ = get_prioritized_methods_groups(
        methods,
        priority_order=priority_order,
    )

    assert priority_order == [
        "A",
        "F",
    ], "The priority_order argument should not be modified by the function"


@pytest.mark.usefixtures("provide_methods_a_f")
def test_get_prioritized_methods_groups():
    methods = get_methods(["A", "B", "C", "D", "E", "F"])
    (MethodA, MethodB, MethodC, MethodD, MethodE, MethodF) = methods

    # Case: Select some methods as more important, with '*'
    assert get_prioritized_methods_groups(methods, priority_order=["A", "F", "*"]) == [
        {MethodA},
        {MethodF},
        {MethodB, MethodC, MethodD, MethodE},
    ]

    # Case: Select some methods as more important, without '*'
    # The results should be exactly the same as with asterisk in the end
    assert get_prioritized_methods_groups(
        methods,
        priority_order=["A", "F"],
    ) == [
        {MethodA},
        {MethodF},
        {MethodB, MethodC, MethodD, MethodE},
    ]

    # Case: asterisk in the middle
    assert get_prioritized_methods_groups(methods, priority_order=["A", "*", "B"]) == [
        {MethodA},
        {MethodC, MethodD, MethodE, MethodF},
        {MethodB},
    ]

    # Case: asterisk at the start
    assert get_prioritized_methods_groups(methods, priority_order=["*", "A", "B"]) == [
        {MethodC, MethodD, MethodE, MethodF},
        {MethodA},
        {MethodB},
    ]

    # Case: Using sets
    assert get_prioritized_methods_groups(
        methods, priority_order=[{"A", "B"}, "*", {"E", "F"}]
    ) == [
        {MethodA, MethodB},
        {MethodC, MethodD},
        {MethodE, MethodF},
    ]

    # Case: Using sets, no asterisk -> implicit asterisk at the end
    assert get_prioritized_methods_groups(methods, priority_order=[{"A", "B"}]) == [
        {MethodA, MethodB},
        {MethodC, MethodD, MethodE, MethodF},
    ]

    # Case: priority_order is None -> Should return all methods as one set
    assert get_prioritized_methods_groups(methods, priority_order=None) == [
        {MethodA, MethodB, MethodC, MethodD, MethodE, MethodF},
    ]
