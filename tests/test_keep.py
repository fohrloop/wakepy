from wakepy import keep


def test_keep_running():
    with keep.running() as k:
        assert k.success
        assert not k.failure


def test_keep_presenting():
    with keep.presenting() as k:
        assert k.success
        assert not k.failure
