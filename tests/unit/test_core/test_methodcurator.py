import re

import pytest

from wakepy.core.methodcurator import MethodCurator


def test_skip_and_use_only_both_given():
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Can only define skip (blacklist) or use_only (whitelist), not both!"
        ),
    ):
        MethodCurator(skip=["A"], use_only=["foo"])
