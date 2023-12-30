import pytest

from wakepy.core import BusType, CallProcessor, DbusAddress, DbusMethod
from wakepy.core.dbus import DbusAdapter
from wakepy.methods.gnome import (
    GnomeFlag,
    GnomeSessionManagerNoIdle,
    GnomeSessionManagerNoSuspend,
)

session_manager = DbusAddress(
    bus=BusType.SESSION,
    service="org.gnome.SessionManager",
    path="org/gnome/SessionManager",
    interface="org.gnome.SessionManager",
)

method_inhibit = DbusMethod(
    name="Inhibit",
    signature="susu",
    params=("app_id", "toplevel_xid", "reason", "flags"),
    output_signature="u",
    output_params=("inhibit_cookie",),
).of(session_manager)

method_uninhibit = DbusMethod(
    name="UnInhibit",
    signature="u",
    params=("inhibit_cookie",),
).of(session_manager)


class DbusGnomeMockAdapter(DbusAdapter):
    def __init__(self):
        super().__init__()
        self.__expected_inhibit_args = {
            "app_id": "wakepy",
            "toplevel_xid": 42,
            "reason": "wakelock active",
            "flags": self._flag,
        }

        self.__expected_uninhibit_args = {
            "inhibit_cookie": self._cookie,
        }

    def process(self, call):
        if call.method == method_inhibit:
            return self.__process_inhibit(call)
        elif call.method == method_uninhibit:
            return self.__process_uninhibit(call)
        raise Exception("should never happen")

    def __process_inhibit(self, call):
        assert call.args == self.__expected_inhibit_args
        return self._cookie

    def __process_uninhibit(self, call):
        assert call.args == self.__expected_uninhibit_args
        self._process_inhibit_called = True


@pytest.mark.parametrize(
    "method_cls, flag",
    [
        (GnomeSessionManagerNoSuspend, GnomeFlag.INHIBIT_SUSPEND),
        (GnomeSessionManagerNoIdle, GnomeFlag.INHIBIT_IDLE),
    ],
)
def test_gnome(method_cls, flag):
    # Setup a mock adapter

    cookie = 75848243423

    class TestAdapter(DbusGnomeMockAdapter):
        _flag = flag
        _cookie = cookie

    call_processor = CallProcessor(dbus_adapter=TestAdapter)
    # Test the method
    method = method_cls(call_processor)

    # Checks before tests
    # Nothing yet set
    assert method.inhibit_cookie is None

    # cannot exit yet as have not entered
    with pytest.raises(ValueError):
        method.exit_mode()

    # 1) Test enter_mode
    # This sets a inhibit_cookie
    method.enter_mode()
    assert method.inhibit_cookie == cookie

    # 2) Test exit_mode
    method.exit_mode()
    assert call_processor.dbus_adapter._process_inhibit_called
    assert method.inhibit_cookie is None
