import re

import pytest

from wakepy.core.activation import (
    check_methods_priority,
    get_prioritized_methods,
    get_prioritized_methods_groups,
    sort_methods_by_priority,
)
from wakepy.core.method import PlatformName, get_methods


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

    # duplicate method names
    with pytest.raises(
        ValueError,
        match=re.escape('Duplicate method name "A" in methods_priority'),
    ):
        check_methods_priority(
            methods_priority=["A", "*", "B", {"A", "C"}], methods=methods
        )

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


@pytest.mark.usefixtures("provide_methods_different_platforms")
def test_sort_methods_by_priority(monkeypatch):
    WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
        ["WinA", "WinB", "WinC", "LinuxA", "LinuxB", "LinuxC", "multiA"]
    )

    monkeypatch.setattr("wakepy.core.activation.CURRENT_PLATFORM", PlatformName.LINUX)
    # Expecting to see Linux methods prioritized, and then by method name
    assert sort_methods_by_priority(
        {WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA}
    ) == [LinuxA, LinuxB, LinuxC, MultiPlatformA, WindowsA, WindowsB, WindowsC]

    monkeypatch.setattr("wakepy.core.activation.CURRENT_PLATFORM", PlatformName.WINDOWS)
    # Expecting to see windows methods prioritized, and then by method name
    assert sort_methods_by_priority(
        {WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA}
    ) == [MultiPlatformA, WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC]


@pytest.mark.usefixtures("provide_methods_different_platforms")
def test_get_prioritized_methods(monkeypatch):
    WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
        ["WinA", "WinB", "WinC", "LinuxA", "LinuxB", "LinuxC", "multiA"]
    )

    monkeypatch.setattr("wakepy.core.activation.CURRENT_PLATFORM", PlatformName.LINUX)

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

    monkeypatch.setattr("wakepy.core.activation.CURRENT_PLATFORM", PlatformName.WINDOWS)
    # No user-defined order -> Just alphabetical, but current platform (Windows) first.
    assert get_prioritized_methods(
        [LinuxA, LinuxB, WindowsA, WindowsB, LinuxC, MultiPlatformA],
    ) == [MultiPlatformA, WindowsA, WindowsB, LinuxA, LinuxB, LinuxC]
