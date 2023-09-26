"""End-to-end testing of the whole package. Use different types of Modes.
"""
from wakepy.core import CURRENT_SYSTEM
from wakepy.core.method import Method, SystemName
from wakepy.core.mode import Mode


class MethodEnterExit(Method):
    supported_systems = (CURRENT_SYSTEM,)

    def enter_mode(self):
        ...

    def exit_mode(self):
        ...


class HeartBeatMethod(Method):
    supported_systems = (CURRENT_SYSTEM,)

    def heartbeat(self):
        ...


class MyMode(Mode):
    methods = [MethodEnterExit, HeartBeatMethod]


def test_that_switching_works():
    mode = MyMode()
    with mode as m:
        assert m.success
