from wakepy.core.method import (
    Method,
    MethodError,
    EnterModeError,
    HeartbeatCallError,
    ExitModeError,
)
import pytest

pytest.skip("These need to be fixed", allow_module_level=True)


def test_overridden_methods_autodiscovery():
    """The enter_mode, heartbeat and exit_mode methods by default do nothing
    (on the Method base class). In subclasses, these are usually overriden.
    Check that detecting the overridden methods works correctly
    """

    class WithEnterAndExit(Method):
        def enter_mode(self):
            return

        def exit_mode(self):
            return

    method1 = WithEnterAndExit()

    assert method1.has_enter
    assert method1.has_exit
    assert not method1.has_heartbeat

    class WithJustHeartBeat(Method):
        def heartbeat(self):
            return

    method2 = WithJustHeartBeat()

    assert not method2.has_enter
    assert not method2.has_exit
    assert method2.has_heartbeat

    class WithEnterExitAndHeartBeat(Method):
        def heartbeat(self):
            return

        def enter_mode(self):
            return

        def exit_mode(self):
            return

    method3 = WithEnterExitAndHeartBeat()

    assert method3.has_enter
    assert method3.has_exit
    assert method3.has_heartbeat

    class SubWithEnterAndHeart(WithJustHeartBeat):
        def enter_mode():
            return

    method4 = SubWithEnterAndHeart()
    assert method4.has_enter
    assert method4.has_heartbeat
    assert not method4.has_exit

    class SubWithEnterAndExit(WithEnterAndExit):
        def enter_mode():
            return 123

    method5 = SubWithEnterAndExit()
    assert method5.has_enter
    assert method5.has_exit
    assert not method5.has_heartbeat


def test_method_has_x_is_not_writeable():
    class MethodWithEnter(Method):
        def enter_mode(self):
            return

    method = MethodWithEnter()
    assert method.has_enter
    assert not method.has_exit

    # The .has_enter, .has_exit or .has_heartbeat should be strictly read-only
    with pytest.raises(AttributeError):
        method.has_enter = False

    with pytest.raises(AttributeError):
        method.has_exit = True

    # Same holds for classes
    with pytest.raises(AttributeError):
        MethodWithEnter.has_enter = False


def test_all_combinations_with_switch_to_the_mode(test_method_classes):
    """This test uses a pytest fixture with automatically generated different
    Method subclasses to test that each of following combinations:

        M{enter_mode}{heartbeat}{exit_mode}

    where each of {enter_mode}, {heartbeat} and {exit_mode} is either
    0: not implemented (missing method)
    1: successful (implemented and not raising exception)
    2: exception (implemented and raising exception)"

    works as expected.
    """
    exception = 2

    for cls_name, method_cls in test_method_classes.items():
        enter_mode, heartbeat, exit_mode = (int(x) for x in cls_name[1:4])
        method = method_cls()

        if cls_name.startswith("M00"):
            # enter_mode and heartbeat both missing -> not possible to switch
            assert not method.activate_the_mode()
            assert isinstance(method.mode_switch_exception, MethodError)
        elif exception not in (enter_mode, heartbeat):
            # When neither enter_mode or heartbeat will cause exception, the
            # switch should be successful
            assert method.activate_the_mode()
            assert method.mode_switch_exception is None
        elif enter_mode == exception:
            # If enter_mode has exception, switch is not successful
            # .. and the exception type is EnterModeError
            assert not method.activate_the_mode()
            assert isinstance(method.mode_switch_exception, EnterModeError)
        elif (heartbeat == exception) and (exit_mode != exception):
            # If heartbeat has exception, switch is not successful
            # .. and the exception type is HeartbeatCallError
            assert not method.activate_the_mode()
            assert isinstance(method.mode_switch_exception, HeartbeatCallError)
        elif (heartbeat == exception) and (exit_mode == exception):
            # If heartbeat has exception, we try to back off by calling
            # exit_mode. If that fails, there should be exception raised.
            with pytest.raises(ExitModeError):
                method.activate_the_mode()
        else:
            # Test case missing? Should not happen ever.
            raise Exception(cls_name)
