import pytest

from wakepy._core import import_module_for_method
from wakepy._core import CURRENT_SYSTEM
from wakepy.constants import (
    SystemName,
    MethodNameWindows,
)


def run_only_on_windows(func):
    return pytest.mark.skipif(
        CURRENT_SYSTEM != SystemName.WINDOWS, reason="This test is only for Windows"
    )(func)


@run_only_on_windows
def test_import_module_windows():
    module = import_module_for_method(SystemName.WINDOWS, MethodNameWindows.ES_FLAGS)
    from wakepy._implementations._windows import _esflags

    assert module is _esflags
