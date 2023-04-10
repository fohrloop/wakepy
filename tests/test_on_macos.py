import pytest

from wakepy._core import import_module_for_method
from wakepy._core import CURRENT_SYSTEM
from wakepy.constants import (
    SystemName,
    MethodNameMac,
)


@pytest.mark.skipif(
    CURRENT_SYSTEM != SystemName.DARWIN, reason="This test is only for macOS"
)
def test_import_module_darwin():
    module = import_module_for_method(SystemName.DARWIN, MethodNameMac.CAFFEINATE)
    from wakepy._implementations._darwin import _caffeinate

    assert module is _caffeinate
