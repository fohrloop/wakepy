import itertools
import re

import pytest

from wakepy.core.method import (
    EnterModeError,
    ExitModeError,
    HeartbeatCallError,
    Method,
    MethodError,
    MethodDefinitionError,
    get_method_class,
)

from testmethods import MethodIs, get_test_method_class


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


def test_get_method_class_which_is_not_yet_defined(monkeypatch):
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    # The method registry is empty so there is no Methods with the name
    with pytest.raises(
        KeyError, match=re.escape('No Method with name "Some name" found!')
    ):
        get_method_class("Some name")


def test_get_method_class_working_example(monkeypatch):
    somename = "Some name"
    # Make the registry empty
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    # Create a method
    class SomeMethod(Method):
        name = somename

    # Check that we can retrieve the method
    method_class = get_method_class(somename)
    assert method_class is SomeMethod


def test_not_possible_to_define_two_methods_with_same_name(monkeypatch):
    somename = "Some name"
    # Make the registry empty
    monkeypatch.setattr("wakepy.core.method.METHOD_REGISTRY", dict())

    class SomeMethod(Method):
        name = somename

    # It is not possible to define two methods if same name
    with pytest.raises(
        MethodDefinitionError, match=re.escape('Duplicate Method name "Some name"')
    ):

        class SomeMethod(Method):
            name = somename


def test_all_combinations_with_switch_to_the_mode():
    """Test that each of following combinations:

        {enter_mode} {heartbeat} {exit_mode}

    where each of {enter_mode}, {heartbeat} and {exit_mode} is either
    0: not implemented (missing method)
    1: successful (implemented and not raising exception)
    2: exception (implemented and raising exception)"

    works as expected.
    """

    for enter_mode, heartbeat, exit_mode in itertools.product(
        (MethodIs.MISSING, MethodIs.SUCCESSFUL, MethodIs.RAISING_EXCEPTION),
        (MethodIs.MISSING, MethodIs.SUCCESSFUL, MethodIs.RAISING_EXCEPTION),
        (MethodIs.MISSING, MethodIs.SUCCESSFUL, MethodIs.RAISING_EXCEPTION),
    ):
        method = get_test_method_class(
            enter_mode=enter_mode, heartbeat=heartbeat, exit_mode=exit_mode
        )()

        if enter_mode == heartbeat == MethodIs.MISSING:
            # enter_mode and heartbeat both missing -> not possible to switch
            assert not method.activate_the_mode()
            assert isinstance(method.mode_switch_exception, MethodError)
            continue
        elif MethodIs.RAISING_EXCEPTION not in (enter_mode, heartbeat):
            # When neither enter_mode or heartbeat will cause exception,
            # the switch should be successful
            assert method.activate_the_mode()
            assert method.mode_switch_exception is None
        elif enter_mode == MethodIs.RAISING_EXCEPTION:
            # If enter_mode has exception, switch is not successful
            # .. and the exception type is EnterModeError
            assert not method.activate_the_mode()
            assert isinstance(method.mode_switch_exception, EnterModeError)
        elif (heartbeat == MethodIs.RAISING_EXCEPTION) and (
            exit_mode != MethodIs.RAISING_EXCEPTION
        ):
            # If heartbeat has exception, switch is not successful
            # .. and the exception type is HeartbeatCallError
            assert not method.activate_the_mode()
            assert isinstance(method.mode_switch_exception, HeartbeatCallError)
        elif (heartbeat == MethodIs.RAISING_EXCEPTION) and (
            exit_mode == MethodIs.RAISING_EXCEPTION
        ):
            # If heartbeat has exception, we try to back off by calling
            # exit_mode. If that fails, there should be exception raised.
            with pytest.raises(ExitModeError):
                method.activate_the_mode()
        else:
            # Test case missing? Should not happen ever.
            raise Exception(method.__class__.__name__)
