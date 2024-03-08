import re

import pytest

from wakepy.core import DBusAddress, DBusMethod, DBusMethodCall


@pytest.fixture
def service():
    return DBusAddress(path="/foo", service="wakepy.foo", interface="/foo")


@pytest.fixture
def method(service):
    return DBusMethod(
        name="test-method", signature="isi", params=("first", "second", "third")
    ).of(service)


@pytest.fixture
def method_without_params(service):
    service = DBusAddress(path="/foo", service="wakepy.foo", interface="/foo")
    return DBusMethod(
        name="test-method",
        signature="isi",
    ).of(service)


def test_dbusmethod_args_none(method: DBusMethod):
    call = DBusMethodCall(method, args=None)
    assert call.args == tuple()


def test_dbusmethod_args_missing(method: DBusMethod):
    call = DBusMethodCall(method)
    assert call.args == tuple()


def test_dbusmethod_args_tuple(method: DBusMethod):
    args = (1, "2", 3)
    call = DBusMethodCall(method, args=args)
    assert call.args == args


def test_dbusmethod_args_tuple_too_long(method: DBusMethod):
    args = (1, "2", 3, 4)
    with pytest.raises(
        ValueError,
        match=re.escape("Expected args to have 3 items! (has: 4)"),
    ):
        DBusMethodCall(method, args=args)


def test_dbusmethod_args_tuple_too_short(method: DBusMethod):
    args = (1, "2")
    with pytest.raises(
        ValueError,
        match=re.escape("Expected args to have 3 items! (has: 2)"),
    ):
        DBusMethodCall(method, args=args)


def test_dbusmethod_args_list(method: DBusMethod):
    args = [1, "2", 3]
    call = DBusMethodCall(method, args=args)
    assert call.args == (1, "2", 3)


def test_dbusmethod_args_dict_method_without_params(
    method_without_params: DBusMethod,
):
    args = dict(first=1, second="2", third=3)
    with pytest.raises(
        ValueError,
        match=re.escape(
            "args cannot be a dictionary if method does not have the params defined! "
            "Either add params to the DBusMethod 'test-method' or give args as a tuple "
            "or a list."
        ),
    ):
        DBusMethodCall(method_without_params, args=args)


def test_dbusmethod_args_dict_too_many_keys(method: DBusMethod):
    args = dict(first=1, second="2", third=3, fourth=4)

    with pytest.raises(
        ValueError,
        match=re.escape("Expected args to have 3 items! (has: 4)"),
    ):
        DBusMethodCall(method, args=args)


def test_dbusmethod_args_dict_too_few_keys(method: DBusMethod):
    args = dict(first=1, second="2")

    with pytest.raises(
        ValueError,
        match=re.escape("Expected args to have 3 items! (has: 2)"),
    ):
        DBusMethodCall(method, args=args)


def test_dbusmethod_args_dict_wrong_keys(method: DBusMethod):
    args = dict(first=1, second="2", fifth="2")

    with pytest.raises(
        ValueError,
        match=re.escape(
            "The keys in `args` do not match the keys in the DBusMethod params! "
            "Expected: ('first', 'second', 'third'). Got: ('first', 'second', 'fifth')"
        ),
    ):
        DBusMethodCall(method, args=args)


def test_dbusmethod_args_dict(method: DBusMethod):
    args = dict(first=1, second="2", third=3)
    call = DBusMethodCall(method, args=args)
    assert call.args == (1, "2", 3)


def test_dbusmethod_args_dict_different_order(method: DBusMethod):
    args = dict(third=3, first=1, second="2")
    call = DBusMethodCall(method, args=args)
    assert call.args == (1, "2", 3)


def test_dbusmethod_get_kwargs(method: DBusMethod):
    args = (1, "2", 3)
    call = DBusMethodCall(method, args=args)
    assert call.get_kwargs() == dict(first=1, second="2", third=3)


def test_dbusmethod_get_kwargs_noparams(method_without_params: DBusMethod):
    args = (1, "2", 3)
    call = DBusMethodCall(method_without_params, args=args)
    # Not possible to convert to args to dict as the params are not named.
    assert call.get_kwargs() is None


def test_dbusmethod_string_representation(method: DBusMethod):
    args = (1, "2", 3)
    call = DBusMethodCall(method, args=args)
    assert call.__repr__() == "<wakepy.foo (1, '2', 3) | bus: SESSION>"
