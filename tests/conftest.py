from typing import Optional

import pytest


@pytest.fixture
def do_assert():
    """Function to be used instead of assert statement."""

    # Fixes issue with mypy: https://github.com/python/mypy/issues/11969
    # In short, when testing and needing to assert that a variable has certain
    # value, and then mutating the value and asserting the value again (
    # against new assumed value), mypy does not handle that case but you'll get
    # [unreachable] errors. Using `do_assert(...)` instead of `assert ...` in
    # tests fixes this.

    def _do_assert(
        expression: bool,
        message: Optional[str] = None,
    ) -> None:
        """Original idea: Nikita Sobolev (safe-assert)[1]. Fixed the return
        type to make this usable[2]

        [1] https://github.com/wemake-services/safe-assert/blob/e3ebfe72a910915e227a9f5447a0f7f56d5219e6/safe_assert/__init__.py
        [2] https://github.com/wemake-services/safe-assert/pull/131
        """
        if not expression:
            if message:
                raise AssertionError(message)
            raise AssertionError

    return _do_assert
