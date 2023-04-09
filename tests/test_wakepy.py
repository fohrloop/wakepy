import pytest

from wakepy._core import import_module_for_method
from wakepy._core import CURRENT_SYSTEM
from wakepy.constants import (
    SystemName,
    MethodNameMac,
    MethodNameLinux,
    MethodNameWindows,
)


def test_run_keepawake():
    from wakepy import set_keepawake, unset_keepawake, keepawake

    set_keepawake()
    unset_keepawake()


@pytest.mark.skipif(
    CURRENT_SYSTEM != SystemName.DARWIN, reason="This test is only for macOS"
)
def test_import_module_darwin():
    module = import_module_for_method(SystemName.DARWIN, MethodNameMac.CAFFEINATE)
    from wakepy._implementations._darwin import _caffeinate

    assert module is _caffeinate


@pytest.mark.skipif(
    CURRENT_SYSTEM != SystemName.WINDOWS, reason="This test is only for Windows"
)
def test_import_module_windows():
    module = import_module_for_method(SystemName.WINDOWS, MethodNameWindows.ES_FLAGS)
    from wakepy._implementations._windows import _esflags

    assert module is _esflags


@pytest.mark.skipif(
    CURRENT_SYSTEM != SystemName.LINUX, reason="This test is only for Linux"
)
def test_import_module_linux():
    module = import_module_for_method(SystemName.LINUX, MethodNameLinux.DBUS)
    from wakepy._implementations._linux import _dbus

    assert module is _dbus
