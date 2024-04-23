import pytest

import wakepy


def test_imports():
    """tests the public API"""
    from wakepy import ActivationError  # noqa: F401
    from wakepy import ActivationResult  # noqa: F401
    from wakepy import JeepneyDBusAdapter  # noqa: F401
    from wakepy import Method  # noqa: F401
    from wakepy import MethodActivationResult  # noqa: F401
    from wakepy import Mode  # noqa: F401
    from wakepy import ModeExit  # noqa: F401
    from wakepy import keep  # noqa: F401


def test_successful_attribute_access():
    """sanity check that the lazy-loading does not mess up anything"""
    wakepy.Method
    wakepy.keep


def test_failing_import():

    with pytest.raises(AttributeError):
        wakepy.something_that_does_not_exist
