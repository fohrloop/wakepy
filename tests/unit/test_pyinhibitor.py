from pathlib import Path

import pytest

import wakepy
from wakepy.pyinhibitor.inhibitors import get_module_path


class TestGetModulePath:

    def test_four_levels(self):
        assert (
            get_module_path("wakepy.methods.gtk.inhibitor")
            == Path(wakepy.__file__).parent / "methods" / "gtk" / "inhibitor.py"
        )

    def test_two_levels(self):
        assert get_module_path("wakepy.foo") == Path(wakepy.__file__).parent / "foo.py"

    def test_bad_path(self):
        with pytest.raises(ValueError):
            get_module_path("foo.bar")
