import pytest

from wakepy._core import import_module_for_method
from wakepy._core import CURRENT_SYSTEM
from wakepy.constants import (
    SystemName,
    MethodNameLinux,
)


@pytest.mark.skipif(
    CURRENT_SYSTEM != SystemName.LINUX, reason="This test is only for Linux"
)
def test_import_module_linux():
    module = import_module_for_method(SystemName.LINUX, MethodNameLinux.DBUS)
    from wakepy._implementations._linux import _dbus

    assert module is _dbus
