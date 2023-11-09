from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import List, Optional, Set, Tuple

    from .method import MethodCls

    MethodClassCollection = List[MethodCls] | Tuple[MethodCls, ...] | Set[MethodCls]
    StrCollection = List[str] | Tuple[str, ...] | Set[str]


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

    skip: Optional[MethodClassCollection]
    use_only: Optional[MethodClassCollection]
    lower_priority: MethodClassCollection
    higher_priority: MethodClassCollection

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
