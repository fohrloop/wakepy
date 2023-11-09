from wakepy.modes import keep

import pytest

pytest.skip("These need to be fixed", allow_module_level=True)


def test_keep_running():
    with keep.running() as k:
        assert k.success
        assert not k.failure


def test_keep_presenting():
    with keep.presenting() as k:
        assert k.success
        assert not k.failure
