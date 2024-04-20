from __future__ import annotations

import re
import typing

import pytest

from wakepy.core import PlatformName
from wakepy.core.prioritization import (
    _order_set_of_methods_by_priority,
    check_methods_priority,
    order_methods_by_priority,
    sort_methods_to_priority_groups,
)
from wakepy.core.registry import get_methods

if typing.TYPE_CHECKING:
    from typing import List, Type

    from wakepy import Method


@pytest.fixture
def set_current_platform_to_linux(monkeypatch):

    monkeypatch.setattr(
        "wakepy.core.prioritization.CURRENT_PLATFORM", PlatformName.LINUX
    )


@pytest.fixture
def set_current_platform_to_windows(monkeypatch):

    monkeypatch.setattr(
        "wakepy.core.prioritization.CURRENT_PLATFORM", PlatformName.WINDOWS
    )


@pytest.mark.usefixtures("provide_methods_different_platforms")
class TestOrderMethodsByPriority:

    @pytest.mark.usefixtures("set_current_platform_to_linux")
    def test_one_method_after_everything_else(self):
        LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
            ["LinuxA", "LinuxB", "LinuxC", "multiA"]
        )

        assert order_methods_by_priority(
            [
                LinuxA,
                LinuxB,
                LinuxC,
                MultiPlatformA,
            ],
            # Means: Prioritize LinuxC after everything else
            methods_priority=["*", {"LinuxC"}],
        ) == [LinuxA, LinuxB, MultiPlatformA, LinuxC]

    @pytest.mark.usefixtures("set_current_platform_to_linux")
    def test_one_method_before_everything_else(self):
        LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
            ["LinuxA", "LinuxB", "LinuxC", "multiA"]
        )

        assert order_methods_by_priority(
            [
                LinuxA,
                LinuxB,
                LinuxC,
                MultiPlatformA,
            ],
            # Means: prioritize LinuxC over anything else.
            methods_priority=[{"LinuxC"}],
        ) == [LinuxC, LinuxA, LinuxB, MultiPlatformA]

    @pytest.mark.usefixtures("set_current_platform_to_linux")
    def test_set_high_and_low_priority_method(self):
        LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
            ["LinuxA", "LinuxB", "LinuxC", "multiA"]
        )
        assert order_methods_by_priority(
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

    @pytest.mark.usefixtures("set_current_platform_to_linux")
    def test_automatic_ordering_by_platform(self):
        WindowsA, LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
            ["WinA", "LinuxA", "LinuxB", "LinuxC", "multiA"]
        )
        assert order_methods_by_priority(
            [LinuxA, LinuxB, LinuxC, MultiPlatformA, WindowsA],
            # Means "LinuxB & WinA" first, ordered with automatic ordering, and
            # then all the rest, also automatically ordered
            methods_priority=[{"WinA", "LinuxB"}, "*"],
        ) == [LinuxB, WindowsA, LinuxA, LinuxC, MultiPlatformA]

    @pytest.mark.usefixtures("set_current_platform_to_linux")
    def test_without_any_user_defined_ordering_on_linux(self):
        WindowsA, WindowsB, LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
            ["WinA", "WinB", "LinuxA", "LinuxB", "LinuxC", "multiA"]
        )

        # No user-defined order -> Just alphabetical, but current platform (linux)
        # first.
        assert order_methods_by_priority(
            [
                LinuxA,
                LinuxB,
                WindowsA,
                WindowsB,
                LinuxC,
                MultiPlatformA,
            ],
        ) == [LinuxA, LinuxB, LinuxC, MultiPlatformA, WindowsA, WindowsB]

    @pytest.mark.usefixtures("set_current_platform_to_windows")
    def test_without_any_user_defined_ordering_on_windows(self):
        WindowsA, WindowsB, LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
            ["WinA", "WinB", "LinuxA", "LinuxB", "LinuxC", "multiA"]
        )
        # No user-defined order -> Just alphabetical, but current platform
        # (Windows) first.
        assert order_methods_by_priority(
            [LinuxA, LinuxB, WindowsA, WindowsB, LinuxC, MultiPlatformA],
        ) == [MultiPlatformA, WindowsA, WindowsB, LinuxA, LinuxB, LinuxC]


@pytest.mark.usefixtures("provide_methods_a_f")
class TestCheckMethodsPriority:

    @staticmethod
    @pytest.fixture
    def methods() -> List[Type[Method]]:
        return get_methods(["A", "B", "C", "D", "E", "F"])

    def test_none(self, methods: List[Type[Method]]):
        check_methods_priority(methods_priority=None, methods=methods)

    def test_empty_list(self, methods: List[Type[Method]]):
        # methods_priority is empty list. Does not crash.
        check_methods_priority(methods_priority=[], methods=methods)

    def test_list_with_just_asterisk(self, methods: List[Type[Method]]):
        # Does not make sense but should not crash.
        check_methods_priority(methods_priority=["*"], methods=methods)

    def test_list_of_few_method_names(self, methods: List[Type[Method]]):
        # Simple list of methods
        check_methods_priority(methods_priority=["A", "B", "F"], methods=methods)

    def test_list_of_few_method_names_and_asterisk(self, methods: List[Type[Method]]):
        # Simple list of methods with asterisk
        check_methods_priority(methods_priority=["A", "B", "*", "F"], methods=methods)

    def test_set_asterisk_methodname(self, methods: List[Type[Method]]):
        # Simple set + strings
        check_methods_priority(methods_priority=[{"A", "B"}, "*", "F"], methods=methods)

    def test_set_asterisk_methodname_set(self, methods: List[Type[Method]]):
        # Simple set + strings
        check_methods_priority(
            methods_priority=[{"A", "B"}, "*", "E", {"F"}], methods=methods
        )

    def test_method_name_which_does_not_exist(self, methods: List[Type[Method]]):
        # There is no Method with name "X" in methods
        with pytest.raises(
            ValueError,
            match=re.escape('Method "X" in methods_priority not in selected methods!'),
        ):
            check_methods_priority(methods_priority=["X"], methods=methods)

    def test_two_asterisks(self, methods: List[Type[Method]]):
        with pytest.raises(
            ValueError,
            match=re.escape(
                "The asterisk (*) can only occur once in methods_priority!"
            ),
        ):
            check_methods_priority(
                methods_priority=["A", "*", "B", "*"], methods=methods
            )

    def test_duplicate_method_names(self, methods: List[Type[Method]]):
        with pytest.raises(
            ValueError,
            match=re.escape('Duplicate method name "A" in methods_priority'),
        ):
            check_methods_priority(
                methods_priority=["A", "*", "B", {"A", "C"}], methods=methods
            )

    def test_asterisk_inside_a_set(self, methods: List[Type[Method]]):
        # Asterisk inside a set
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Asterisk (*) may not be a part of a set in methods_priority!"
            ),
        ):
            check_methods_priority(methods_priority=[{"*"}], methods=methods)

    def test_list_of_methods_as_methods_priority(self, methods: List[Type[Method]]):
        (MethodA, *_) = methods
        with pytest.raises(
            TypeError,
            match=re.escape("methods_priority must be a list[str | set[str]]!"),
        ):
            check_methods_priority(
                methods_priority=[MethodA],  # type: ignore
                methods=methods,
            )


@pytest.mark.usefixtures("provide_methods_a_f")
def test_sort_methods_to_priority_groups_does_not_edit_args():
    """Test that the prioriry_order argument is not modified by the function"""
    methods = get_methods(["A", "B", "C", "D", "E", "F"])

    methods_priority = ["A", "F"]

    _ = sort_methods_to_priority_groups(
        methods,
        methods_priority=methods_priority,
    )

    assert methods_priority == [
        "A",
        "F",
    ], "The methods_priority argument should not be modified by the function"


@pytest.mark.usefixtures("provide_methods_a_f")
def test_sort_methods_to_priority_groups():
    methods = get_methods(["A", "B", "C", "D", "E", "F"])
    (MethodA, MethodB, MethodC, MethodD, MethodE, MethodF) = methods

    # Case: Select some methods as more important, with '*'
    assert sort_methods_to_priority_groups(
        methods, methods_priority=["A", "F", "*"]
    ) == [
        {MethodA},
        {MethodF},
        {MethodB, MethodC, MethodD, MethodE},
    ]

    # Case: Select some methods as more important, without '*'
    # The results should be exactly the same as with asterisk in the end
    assert sort_methods_to_priority_groups(
        methods,
        methods_priority=["A", "F"],
    ) == [
        {MethodA},
        {MethodF},
        {MethodB, MethodC, MethodD, MethodE},
    ]

    # Case: asterisk in the middle
    assert sort_methods_to_priority_groups(
        methods, methods_priority=["A", "*", "B"]
    ) == [
        {MethodA},
        {MethodC, MethodD, MethodE, MethodF},
        {MethodB},
    ]

    # Case: asterisk at the start
    assert sort_methods_to_priority_groups(
        methods, methods_priority=["*", "A", "B"]
    ) == [
        {MethodC, MethodD, MethodE, MethodF},
        {MethodA},
        {MethodB},
    ]

    # Case: Using sets
    assert sort_methods_to_priority_groups(
        methods, methods_priority=[{"A", "B"}, "*", {"E", "F"}]
    ) == [
        {MethodA, MethodB},
        {MethodC, MethodD},
        {MethodE, MethodF},
    ]

    # Case: Using sets, no asterisk -> implicit asterisk at the end
    assert sort_methods_to_priority_groups(methods, methods_priority=[{"A", "B"}]) == [
        {MethodA, MethodB},
        {MethodC, MethodD, MethodE, MethodF},
    ]

    # Case: methods_priority is None -> Should return all methods as one set
    assert sort_methods_to_priority_groups(methods, methods_priority=None) == [
        {MethodA, MethodB, MethodC, MethodD, MethodE, MethodF},
    ]


@pytest.mark.usefixtures("provide_methods_different_platforms")
def test__order_set_of_methods_by_priority(monkeypatch):
    WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA = get_methods(
        ["WinA", "WinB", "WinC", "LinuxA", "LinuxB", "LinuxC", "multiA"]
    )

    monkeypatch.setattr("wakepy.core.mode.CURRENT_PLATFORM", PlatformName.LINUX)
    # Expecting to see Linux methods prioritized, and then by method name
    assert _order_set_of_methods_by_priority(
        {WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA}
    ) == [LinuxA, LinuxB, LinuxC, MultiPlatformA, WindowsA, WindowsB, WindowsC]

    monkeypatch.setattr("wakepy.core.mode.CURRENT_PLATFORM", PlatformName.WINDOWS)
    # Expecting to see windows methods prioritized, and then by method name
    assert _order_set_of_methods_by_priority(
        {WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC, MultiPlatformA}
    ) == [MultiPlatformA, WindowsA, WindowsB, WindowsC, LinuxA, LinuxB, LinuxC]
