from wakepy.core.method import Method
from wakepy.core.modeactivator import sort_methods_by_priority


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
