from wakepy.core import DbusMethod, DbusMethodCall, DbusAddress
import pytest


@pytest.fixture
def method():
    service = DbusAddress(path="/foo", service="wakepy.foo", interface="/foo")
    return DbusMethod(
        name="test-method", signature="isi", params=("first", "second", "third")
    ).of(service)


def test_dbusmethod_args_as_tuple_using_tuple(method: DbusMethod):
    args = (1, "2", 3)
    call = DbusMethodCall(method, args=args)
    assert call._args_as_tuple(args, method) == args


def test_dbusmethod_args_as_tuple_using_list(method: DbusMethod):
    args = [1, "2", 3]
    call = DbusMethodCall(method, args=args)
    assert call._args_as_tuple(args, method) == (1, "2", 3)
