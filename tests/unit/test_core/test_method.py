import itertools
import re

import pytest
from testmethods import MethodIs, get_test_method_class

from wakepy.core.method import (
    EnterModeError,
    ExitModeError,
    HeartbeatCallError,
    Method,
    MethodDefinitionError,
    MethodError,
    SystemName,
    check_methods_priority,
    get_method,
    get_methods,
    get_methods_for_mode,
    get_prioritized_methods,
    get_prioritized_methods_groups,
    method_names_to_classes,
    select_methods,
    sort_methods_by_priority,
)

# B, D, E
FIRST_MODE = "first_mode"
# A, F
SECOND_MODE = "second_mode"


@pytest.fixture(scope="function")
def provide_methods_a_f(monkeypatch):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    class MethodA(Method):
        name = "A"
        mode = SECOND_MODE

    class MethodB(Method):
        name = "B"
        mode = FIRST_MODE

    class MethodC(Method):
        name = "C"

    class MethodD(Method):
        name = "D"
        mode = FIRST_MODE

    class MethodE(Method):
        name = "E"
        mode = FIRST_MODE

    class MethodF(Method):
        name = "F"
        mode = SECOND_MODE


@pytest.fixture(scope="function")
def provide_methods_different_systems(monkeypatch):
    # empty method registry
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    class WindowsA(Method):
        name = "WinA"
        supported_platforms = (SystemName.WINDOWS,)

    class WindowsB(Method):
        name = "WinB"
        supported_platforms = (SystemName.WINDOWS,)

    class WindowsC(Method):
        name = "WinC"
        supported_platforms = (SystemName.WINDOWS,)

    class LinuxA(Method):
        name = "LinuxA"
        supported_platforms = (SystemName.LINUX,)

    class LinuxB(Method):
        name = "LinuxB"
        supported_platforms = (SystemName.LINUX,)

    class LinuxC(Method):
        name = "LinuxC"
        supported_platforms = (SystemName.LINUX,)

    class MultiPlatformA(Method):
        name = "multiA"
        supported_platforms = (SystemName.LINUX, SystemName.WINDOWS, SystemName.DARWIN)


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


@pytest.mark.usefixtures("provide_methods_a_f")
def test_get_methods_for_mode():
    methods = get_methods(["A", "B", "C", "D", "E", "F"])
    (MethodA, MethodB, _, MethodD, MethodE, MethodF) = methods

    assert get_methods_for_mode(FIRST_MODE) == [
        MethodB,
        MethodD,
        MethodE,
    ]
    assert get_methods_for_mode(SECOND_MODE) == [
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


@pytest.mark.usefixtures("provide_methods_a_f")
def test_check_methods_priority():
    methods = get_methods(["A", "B", "C", "D", "E", "F"])
    (MethodA, *_) = methods

    # These should be fine
    check_methods_priority(methods_priority=None, methods=methods)
    check_methods_priority(methods_priority=["*"], methods=methods)
    # Simple list of methods
    check_methods_priority(methods_priority=["A", "B", "F"], methods=methods)
    # Simple list of methods with asterisk
    check_methods_priority(methods_priority=["A", "B", "*", "F"], methods=methods)
    # Simple set + strings
    check_methods_priority(methods_priority=[{"A", "B"}, "*", "F"], methods=methods)
    # Simple set + strings
    check_methods_priority(
        methods_priority=[{"A", "B"}, "*", "E", {"F"}], methods=methods
    )

    # These are not fine
    # There is no Method with name "X" in methods
    with pytest.raises(
        ValueError,
        match=re.escape('Method "X" in methods_priority not in selected methods!'),
    ):
        check_methods_priority(methods_priority=["X"], methods=methods)

    # two asterisks
    with pytest.raises(
        ValueError,
        match=re.escape("The asterisk (*) can only occur once in methods_priority!"),
    ):
        check_methods_priority(methods_priority=["A", "*", "B", "*"], methods=methods)

    # Asterisk inside a set
    with pytest.raises(
        ValueError,
        match=re.escape("Asterisk (*) may not be a part of a set in methods_priority!"),
    ):
        check_methods_priority(methods_priority=[{"*"}], methods=methods)

    # Unsupported type
    with pytest.raises(
        TypeError,
        match=re.escape("methods_priority must be a list[str | set[str]]!"),
    ):
        check_methods_priority(methods_priority=[MethodA], methods=methods)


@pytest.mark.usefixtures("provide_methods_a_f")
def test_get_prioritized_methods_groups_does_not_edit_args():
    """Test that the prioriry_order argument is not modified by the function"""
    methods = get_methods(["A", "B", "C", "D", "E", "F"])

    methods_priority = ["A", "F"]

    _ = get_prioritized_methods_groups(
        methods,
        methods_priority=methods_priority,
    )

    assert methods_priority == [
        "A",
        "F",
    ], "The methods_priority argument should not be modified by the function"


@pytest.mark.usefixtures("provide_methods_a_f")
def test_get_prioritized_methods_groups():
    methods = get_methods(["A", "B", "C", "D", "E", "F"])
    (MethodA, MethodB, MethodC, MethodD, MethodE, MethodF) = methods

    # Case: Select some methods as more important, with '*'
    assert get_prioritized_methods_groups(
        methods, methods_priority=["A", "F", "*"]
    ) == [
        {MethodA},
        {MethodF},
        {MethodB, MethodC, MethodD, MethodE},
    ]

    # Case: Select some methods as more important, without '*'
    # The results should be exactly the same as with asterisk in the end
    assert get_prioritized_methods_groups(
        methods,
        methods_priority=["A", "F"],
    ) == [
        {MethodA},
        {MethodF},
        {MethodB, MethodC, MethodD, MethodE},
    ]

    # Case: asterisk in the middle
    assert get_prioritized_methods_groups(
        methods, methods_priority=["A", "*", "B"]
    ) == [
        {MethodA},
        {MethodC, MethodD, MethodE, MethodF},
        {MethodB},
    ]

    # Case: asterisk at the start
    assert get_prioritized_methods_groups(
        methods, methods_priority=["*", "A", "B"]
    ) == [
        {MethodC, MethodD, MethodE, MethodF},
        {MethodA},
        {MethodB},
    ]

    # Case: Using sets
    assert get_prioritized_methods_groups(
        methods, methods_priority=[{"A", "B"}, "*", {"E", "F"}]
    ) == [
        {MethodA, MethodB},
        {MethodC, MethodD},
        {MethodE, MethodF},
    ]

    # Case: Using sets, no asterisk -> implicit asterisk at the end
    assert get_prioritized_methods_groups(methods, methods_priority=[{"A", "B"}]) == [
        {MethodA, MethodB},
        {MethodC, MethodD, MethodE, MethodF},
    ]

    # Case: methods_priority is None -> Should return all methods as one set
    assert get_prioritized_methods_groups(methods, methods_priority=None) == [
        {MethodA, MethodB, MethodC, MethodD, MethodE, MethodF},
    ]


@pytest.mark.usefixtures("provide_methods_different_systems")
def test_sort_methods_by_priority(monkeypatch):
    WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
        ["WinA", "WinB", "WinC", "LinuxA", "LinuxB", "LinuxC", "multiA"]
    )

    monkeypatch.setattr("wakepy.core.method.CURRENT_SYSTEM", SystemName.LINUX)
    # Expecting to see Linux methods prioritized, and then by method name
    assert sort_methods_by_priority(
        {WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA}
    ) == [LinuxA, LinuxB, LinuxC, MultiPlatformA, WindowsA, WindowsB, WindowsC]

    monkeypatch.setattr("wakepy.core.method.CURRENT_SYSTEM", SystemName.WINDOWS)
    # Expecting to see windows methods prioritized, and then by method name
    assert sort_methods_by_priority(
        {WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA}
    ) == [MultiPlatformA, WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC]


@pytest.mark.usefixtures("provide_methods_different_systems")
def test_get_prioritized_methods(monkeypatch):
    WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
        ["WinA", "WinB", "WinC", "LinuxA", "LinuxB", "LinuxC", "multiA"]
    )

    monkeypatch.setattr("wakepy.core.method.CURRENT_SYSTEM", SystemName.LINUX)

    assert get_prioritized_methods(
        [
            LinuxA,
            LinuxB,
            LinuxC,
            MultiPlatformA,
        ],
        # Means: Prioritize LinuxC after everything else
        methods_priority=["*", {"LinuxC"}],
    ) == [LinuxA, LinuxB, MultiPlatformA, LinuxC]

    assert get_prioritized_methods(
        [
            LinuxA,
            LinuxB,
            LinuxC,
            MultiPlatformA,
        ],
        # Means: prioritize LinuxC over anything else.
        methods_priority=[{"LinuxC"}],
    ) == [LinuxC, LinuxA, LinuxB, MultiPlatformA]

    assert get_prioritized_methods(
        [
            LinuxA,
            LinuxB,
            LinuxC,
            MultiPlatformA,
        ],
        # Means, LinuxB first, then anything that is in between, and give
        # lowest priority to LinuxA and LinuxC
        methods_priority=[{"LinuxB"}, "*", {"LinuxA", "LinuxC"}],
    ) == [LinuxB, MultiPlatformA, LinuxA, LinuxC]

    assert get_prioritized_methods(
        [LinuxA, LinuxB, LinuxC, MultiPlatformA, WindowsA],
        # Means "LinuxB & WinA" first, ordered with automatic ordering, and
        # then all the rest, also automatically ordered
        methods_priority=[{"WinA", "LinuxB"}, "*"],
    ) == [LinuxB, WindowsA, LinuxA, LinuxC, MultiPlatformA]

    # No user-defined order -> Just alphabetical, but current platform (linux) first.
    assert get_prioritized_methods(
        [
            LinuxA,
            LinuxB,
            WindowsA,
            WindowsB,
            LinuxC,
            MultiPlatformA,
        ],
    ) == [LinuxA, LinuxB, LinuxC, MultiPlatformA, WindowsA, WindowsB]

    monkeypatch.setattr("wakepy.core.method.CURRENT_SYSTEM", SystemName.WINDOWS)
    # No user-defined order -> Just alphabetical, but current platform (Windows) first.
    assert get_prioritized_methods(
        [LinuxA, LinuxB, WindowsA, WindowsB, LinuxC, MultiPlatformA],
    ) == [MultiPlatformA, WindowsA, WindowsB, LinuxA, LinuxB, LinuxC]
