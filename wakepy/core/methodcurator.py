from __future__ import annotations

import typing

from .method import get_method_classes

if typing.TYPE_CHECKING:
    from typing import List, Optional, Set, Tuple, Type, TypeVar

    from .method import Method

    MethodCls = Type[Method]
    T = TypeVar("T")
    Collection = List[T] | Tuple[T, ...] | Set[T]
    StrCollection = Collection[str]
    MethodClsCollection = Collection[MethodCls]


class MethodCurator:
    """The MethodCurator is used to select and prioritize Methods.

    Purpose
    -------
    1) Handling method selection and prioritization parameters
    * Act as a data storage to method selection and prioritization parameters.
    * Provide basic validation for those input parameters
    * Convert those input parameters from strings to Method classes

    2) Selecting Methods
    * Provide means to select a subset of methods

    3) Prioritizing Methods
    * Provide means to prioritize a collection of methods.
    """

    skip: Optional[MethodClsCollection]
    use_only: Optional[MethodClsCollection]
    lower_priority: Optional[MethodClsCollection]
    higher_priority: Optional[MethodClsCollection]

    def __init__(
        self,
        skip: Optional[StrCollection] = None,
        use_only: Optional[StrCollection] = None,
        lower_priority: Optional[StrCollection] = None,
        higher_priority: Optional[StrCollection] = None,
    ):
        if skip and use_only:
            raise ValueError(
                "Can only define skip (blacklist) or use_only (whitelist), not both!"
            )
        self.skip = get_method_classes(skip)
        self.use_only = get_method_classes(use_only)
        self.lower_priority = get_method_classes(lower_priority)
        self.higher_priority = get_method_classes(higher_priority)
