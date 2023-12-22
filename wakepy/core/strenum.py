"""This module defines StrEnum for making string enumerations.

NOTE: The enum.StrEnum could be used in place of StrEnum on Python 3.11
onwards, so consider removing this module when python 3.10 is no longer
supported."""

from __future__ import annotations

from enum import Enum, EnumMeta, auto
from types import MappingProxyType
from typing import Any


class ConstantEnumMeta(EnumMeta):
    """This metaclass is an extension of the basic Enum metaclass, and provides
    the following

    1) Containment check for enumeration member values; `val in SomeClass`
    2) `unique` parameter when creating constants.
    3) Support for (custom) string-type members in Enums
    """

    @classmethod
    def __prepare__(metacls, clsname, bases, **_):
        # This is needed since we have to allow passing kwargs to __init__
        # Needed on 3.7.x, not needed on 3.10. (not tested 3.8 & 3.9)
        return super().__prepare__(clsname, bases)

    def __new__(metacls, clsname, bases, classdict, **_):
        # This is needed since we have to allow passing kwargs to __init__
        return super().__new__(metacls, clsname, bases, classdict)

    def __init__(cls, *_, unique=False):
        if unique:
            cls._check_uniqueness()

        cls.__members__: MappingProxyType[str, Any]
        for member in cls.__members__.values():
            # The .name is needed for the @unique decorator compatibility
            # It is also part of enum member protocol, so let it be.
            member.name = member._name_

    def _check_uniqueness(cls):
        vals = cls.__members__.values()
        if len(vals) > len(set(vals)):
            raise ValueError("The values must be unique!")

    def __contains__(self, value: Any) -> bool:
        """Provides the `val in SomeConstClass` containment check

        Parameters
        ----------
        self:
            This will be the (subclass) of the class using ConstantEnumMeta.
            If you use class Const(metaclass=ConstantEnumMeta): ... and
            SomeConst(Const), self will be SomeConst; a class.
        value:
            The `val` in the example
        """
        return value in self.__members__.values()

    @property
    def keys(self):
        return self.__members__.keys()

    @property
    def values(self):
        return self.__members__.values


class EnumMemberString(str):
    """dummy string subclass to make it possible to add custom attributes to
    it.
    """


class StrEnum(Enum, metaclass=ConstantEnumMeta):
    """A string constant / enumeration. For creating reusable, typed constants.

    Properties
    -----------

    1) All enumeration members are (subtype of) strings; they can be used
    directly as strings, without the need for the typical member.value type
    of accessing pattern.

    2) All enumeration members can have automatical name:

    >>> from enum import auto
    >>>
    >>> class MyConst(StrEnum):
    ...     BAR = auto()

    >>> MyConst.BAR == "BAR"
    True

    3) Possibility to make values unique; for example

    >>> class MyConst(StrEnum, unique=True):
    ...     FIRST = 'foo'
    ...     SECOND = 'foo'

        ValueError: The values must be unique!


    4) Testing for containment looks for *values*; for example

    >>> class MyConst(StrEnum):
    ...     FOO = 'bar'

    >>> 'bar' in MyConst
    True

    """

    def _generate_next_value_(name, *_):
        """Turn auto() value to be a string corresponding to the enumeration
        member name

        Ref: https://docs.python.org/3/library/enum.html#enum.Enum._generate_next_value_
        """
        return name

    def __new__(cls, val=None, *args):
        """This is used to get rid of need for ".value" access:

        >>> StrEnum.FOO.value
        'foo'

        It is possible to use

        >>> StrEnum.FOO
        'foo'

        instead
        """
        return EnumMemberString(val)


__all__ = [
    "StrEnum",
    "auto",
]
