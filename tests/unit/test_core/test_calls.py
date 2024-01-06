import re

import pytest

from wakepy.core import DbusAddress, DbusMethod, DbusMethodCall


@pytest.fixture
def service():
    return DbusAddress(path="/foo", service="wakepy.foo", interface="/foo")


@pytest.fixture
def method(service):
    return DbusMethod(
        name="test-method", signature="isi", params=("first", "second", "third")
    ).of(service)


@pytest.fixture
def method_without_params(service):
    service = DbusAddress(path="/foo", service="wakepy.foo", interface="/foo")
    return DbusMethod(
        name="test-method",
        signature="isi",
    ).of(service)


def test_dbusmethod_args_tuple(method: DbusMethod):
    args = (1, "2", 3)
    call = DbusMethodCall(method, args=args)
    assert call.args == args


def test_dbusmethod_args_tuple_too_long(method: DbusMethod):
    args = (1, "2", 3, 4)
    with pytest.raises(
        ValueError,
        match=re.escape("Expected args to have 3 items! (has: 4)"),
    ):
        DbusMethodCall(method, args=args)


def test_dbusmethod_args_tuple_too_short(method: DbusMethod):
    args = (1, "2")
    with pytest.raises(
        ValueError,
        match=re.escape("Expected args to have 3 items! (has: 2)"),
    ):
        DbusMethodCall(method, args=args)


def test_dbusmethod_args_list(method: DbusMethod):
    args = [1, "2", 3]
    call = DbusMethodCall(method, args=args)
    assert call.args == (1, "2", 3)


def test_dbusmethod_args_dict_method_without_params(
    method_without_params: DbusMethod,
):
    args = dict(first=1, second="2", third=3)
    with pytest.raises(
        ValueError,
        match=re.escape(
            "args cannot be a dictionary if method does not have the params defined! "
            "Either add params to the DbusMethod 'test-method' or give args as a tuple "
            "or a list."
        ),
    ):
        DbusMethodCall(method_without_params, args=args)


def test_dbusmethod_args_dict_too_many_keys(method: DbusMethod):
    args = dict(first=1, second="2", third=3, fourth=4)

    with pytest.raises(
        ValueError,
        match=re.escape("Expected args to have 3 items! (has: 4)"),
    ):
        DbusMethodCall(method, args=args)


def test_dbusmethod_args_dict_too_few_keys(method: DbusMethod):
    args = dict(first=1, second="2")

    with pytest.raises(
        ValueError,
        match=re.escape("Expected args to have 3 items! (has: 2)"),
    ):
        DbusMethodCall(method, args=args)


def test_dbusmethod_args_dict_wrong_keys(method: DbusMethod):
    args = dict(first=1, second="2", fifth="2")

    with pytest.raises(
        ValueError,
        match=re.escape(
            "The keys in `args` do not match the keys in the DbusMethod params! "
            "Expected: ('first', 'second', 'third'). Got: ('first', 'second', 'fifth')"
        ),
    ):
        DbusMethodCall(method, args=args)


def test_dbusmethod_args_dict(method: DbusMethod):
    args = dict(first=1, second="2", third=3)
    call = DbusMethodCall(method, args=args)
    assert call.args == (1, "2", 3)


def test_dbusmethod_args_dict_different_order(method: DbusMethod):
    args = dict(third=3, first=1, second="2")
    call = DbusMethodCall(method, args=args)
    assert call.args == (1, "2", 3)


def test_dbusmethod_get_kwargs(method: DbusMethod):
    args = (1, "2", 3)
    call = DbusMethodCall(method, args=args)
    assert call.get_kwargs() == dict(first=1, second="2", third=3)


def test_dbusmethod_get_kwargs_noparams(method_without_params: DbusMethod):
    args = (1, "2", 3)
    call = DbusMethodCall(method_without_params, args=args)
    # Not possible to convert to args to dict as the params are not named.
    assert call.get_kwargs() is None


def test_dbusmethod_string_representation(method: DbusMethod):
    args = (1, "2", 3)
    call = DbusMethodCall(method, args=args)
    assert call.__repr__() == "<wakepy.foo (1, '2', 3) | bus: SESSION>"
