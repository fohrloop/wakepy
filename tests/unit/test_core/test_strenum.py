from enum import auto

import pytest

from wakepy.core.strenum import StrEnum


def test_strenum_basic_functionality():
    class MyConst(StrEnum):
        FOO = "fooval"

    # Any string valued constant is
    # added as a string
    assert MyConst.FOO == "fooval"
    assert isinstance(MyConst.FOO, str)
    assert MyConst.FOO.name == "FOO"
    assert MyConst.FOO.value == "fooval"
    # Test containement
    # Values can be querid with in operator
    assert "fooval" in MyConst
    # Names cannot be queried with in operator
    assert "FOO" not in MyConst
    # .. but they could be queried with this
    assert "FOO" in MyConst.__members__.keys()


def test_strenum_auto():
    class MyConst(StrEnum):
        BAR = auto()

    # Any auto() value is turned into a string which is same as
    # the enumeration member name
    assert MyConst.BAR == "BAR"
    assert "BAR" == MyConst.BAR

    assert isinstance(MyConst.BAR, str)


def test_strenum_uniqueness_with_unique_values():
    # This should cause no problems
    class MyConst(StrEnum, unique=True):
        FOO = "fooval"
        BAR = "barval"


def test_strenum_uniqueness_with_non_unique_values():
    # This should raise exception as the 'fooval' value is used twice and
    # uniqueness is asked
    with pytest.raises(ValueError):

        class MyConst(StrEnum, unique=True):
            FOO = "fooval"
            BAR = "fooval"


def test_strenum_duplicates_non_unique_constraint():
    # It should be possible to define duplicate values if uniqueness is not
    # asked
    class MyConst(StrEnum):
        FOO = "fooval"
        ANOTHER_FOO = "fooval"

    assert MyConst.ANOTHER_FOO == "fooval"


def test_keys_and_values():
    class MyConst(StrEnum):
        FOO = "fooval"
        ANOTHER = "another_val"

    expected = dict(FOO="fooval", ANOTHER="another_val")
    assert MyConst.keys() == expected.keys()
    assert list(MyConst.values()) == list(expected.values())
