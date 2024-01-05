from wakepy.core import DbusMethod, DbusMethodCall, DbusAddress
import pytest
import re


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


def test_dbusmethod_args_as_tuple_using_tuple(method: DbusMethod):
    args = (1, "2", 3)
    call = DbusMethodCall(method, args=args)
    assert call._args_as_tuple(args, method) == args


def test_dbusmethod_args_as_tuple_using_list(method: DbusMethod):
    args = [1, "2", 3]
    call = DbusMethodCall(method, args=args)
    assert call._args_as_tuple(args, method) == (1, "2", 3)


def test_dbusmethod_args_as_tuple_using_dict_method_without_params(
    method_without_params: DbusMethod,
):
    args = dict(first=1, second="2", third=3)
    with pytest.raises(
        ValueError,
        match=re.escape(
            "args cannot be a dictionary if method does not have the params defined! Either add params to the DbusMethod 'test-method' or give args as a tuple or a list."
        ),
    ):
        DbusMethodCall(method_without_params, args=args)


def test_dbusmethod_args_dict_too_many_keys(method: DbusMethod):
    args = dict(first=1, second="2", third=3, fourth=4)

    with pytest.raises(
        ValueError,
        match=re.escape("Expected args to have 3 keys! (has: 4)"),
    ):
        DbusMethodCall(method, args=args)


def test_dbusmethod_args_dict_too_few_keys(method: DbusMethod):
    args = dict(first=1, second="2")

    with pytest.raises(
        ValueError,
        match=re.escape("Expected args to have 3 keys! (has: 2)"),
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
