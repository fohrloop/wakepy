from wakepy.core.mode import sort_methods_by_priority, Mode
from wakepy.core.method import Method


def test_sort_methods_by_priority():
    class LinuxMethod(Method):
        ...

    class LinuxMethod2(Method):
        ...

    class WinMethod(Method):
        ...

    class MacLinuxMethod(Method):
        ...

    class MacMethod(Method):
        ...

    methods = [
        LinuxMethod,
        LinuxMethod2,
        WinMethod,
        MacLinuxMethod,
        MacMethod,
    ]

    # No sort.
    assert sort_methods_by_priority(methods) == [
        LinuxMethod,
        LinuxMethod2,
        WinMethod,
        MacLinuxMethod,
        MacMethod,
    ]

    # Now, test getting in order

    assert sort_methods_by_priority(methods, prioritize=[LinuxMethod2]) == [
        LinuxMethod2,
        LinuxMethod,
        WinMethod,
        MacLinuxMethod,
        MacMethod,
    ]
    assert sort_methods_by_priority(
        methods, prioritize=[LinuxMethod2, MacLinuxMethod]
    ) == [
        LinuxMethod2,
        MacLinuxMethod,
        LinuxMethod,
        WinMethod,
        MacMethod,
    ]

    assert sort_methods_by_priority(
        methods,
        prioritize=["foo", MacLinuxMethod, WinMethod, "foo"],
    ) == [
        MacLinuxMethod,
        WinMethod,
        LinuxMethod,
        LinuxMethod2,
        MacMethod,
    ]


def test_prioritizing_methods_in_mode():
    class FirstMethod(Method):
        ...

    class SecondMethod(Method):
        ...

    class ThirdMethod(Method):
        ...

    class SomeMode(Mode):
        methods = [
            FirstMethod,
            SecondMethod,
            ThirdMethod,
        ]

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

    mode = SomeMode(prioritize=[ThirdMethod])

    assert mode._get_method_classes() == [ThirdMethod, FirstMethod, SecondMethod]
