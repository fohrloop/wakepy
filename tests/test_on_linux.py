import pytest
from unittest.mock import patch

from wakepy import keepawake, set_keepawake, unset_keepawake

from wakepy._core import import_module_for_method
from wakepy._core import CURRENT_SYSTEM
from wakepy.constants import (
    SystemName,
    MethodNameLinux,
)


def run_only_on_linux(func):
    return pytest.mark.skipif(
        CURRENT_SYSTEM != SystemName.LINUX, reason="This test is only for Linux"
    )(func)


@run_only_on_linux
def test_import_module_linux():
    module = import_module_for_method(SystemName.LINUX, MethodNameLinux.DBUS)
    from wakepy._implementations._linux import _dbus

    assert module is _dbus


@patch("wakepy._implementations._linux._dbus.unset_keepawake")
@patch("wakepy._implementations._linux._dbus.set_keepawake")
@run_only_on_linux
def test_keepawake_context_manager(set_keepawake_mock, unset_keepawake_mock):
    # The keepawake should call set_keepawake exactly once
    # and only call unset_keepawake after the with block
    #
    # Since we are on Linux, the default is to use methods from
    #   wakepy._implementations._linux._dbus
    #
    with keepawake():
        set_keepawake_mock.assert_called_once()
        unset_keepawake_mock.assert_not_called()

    set_keepawake_mock.assert_called_once()
    unset_keepawake_mock.assert_called_once()


@patch("wakepy._implementations._linux._systemd.unset_keepawake")
@patch("wakepy._implementations._linux._systemd.set_keepawake")
@patch("wakepy._implementations._linux._libdbus.unset_keepawake")
@patch("wakepy._implementations._linux._libdbus.set_keepawake")
@patch("wakepy._implementations._linux._dbus.unset_keepawake")
@patch("wakepy._implementations._linux._dbus.set_keepawake")
@run_only_on_linux
def test_keepawake_with_different_method_order(
    set_keepawake_dbus,
    unset_keepawake_dbus,
    set_keepawake_libdbus,
    unset_keepawake_libdbus,
    set_keepawake_systemd,
    unset_keepawake_systemd,
):
    """Test multiple different scenarios"""

    # Because we mock all of the versions, the first one, systemd, should
    # work. Therefore, no other set_ or unset_keepawakes are called
    # This deviates from the default order, so that's also tested here.
    with keepawake(method_linux=["systemd", "dbus"]):
        set_keepawake_dbus.assert_not_called()
        unset_keepawake_dbus.assert_not_called()
        set_keepawake_libdbus.assert_not_called()
        unset_keepawake_libdbus.assert_not_called()
        set_keepawake_systemd.assert_called_once()  # only this is called!
        unset_keepawake_systemd.assert_not_called()

    set_keepawake_dbus.assert_not_called()
    unset_keepawake_dbus.assert_not_called()
    set_keepawake_libdbus.assert_not_called()
    unset_keepawake_libdbus.assert_not_called()
    set_keepawake_systemd.assert_called_once()  # only this is called!
    unset_keepawake_systemd.assert_called_once()  # only this is called!
