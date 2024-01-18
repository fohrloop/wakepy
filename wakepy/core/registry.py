"""This module constains registry of wakepy.Methods. All the subclasses of
wakepy.Method are automatically added to this registry. The registry can be
accessed with the functions listed below.

Functions for getting Methods
-----------------------------
get_method
    Get a single method by name
get_methods
    Get multiple methods be name
method_names_to_classes
    Convert multiple method names to Method classes
get_methods_for_mode
    Get Methods based on a Mode name
"""

from __future__ import annotations

import typing
from typing import List, Set, Tuple, Type, TypeVar, Union

from .constants import ModeName

if typing.TYPE_CHECKING:
    from wakepy.core.method import Method, MethodCls

T = TypeVar("T")
Collection = Union[List[T], Tuple[T, ...], Set[T]]

_method_registry: dict[str, MethodCls] = dict()
"""A name -> Method class mapping. Updated automatically; when python loads
a module with a subclass of Method, the Method class is added to this registry.
"""


class MethodRegistryError(RuntimeError):
    """Any error which is related to the method registry"""


def register_method(cls: Type[Method]):
    """Registers a subclass of Method to the method registry"""

    if cls.name is None:
        # Methods without a name will not be registered
        return

    if cls.name in _method_registry:
        if _method_registry[cls.name] is not cls:
            raise MethodRegistryError(
                f'Duplicate Method name "{cls.name}": {cls.__qualname__} '
                f"(already registered to {_method_registry[cls.name].__qualname__})"
            )
        else:
            return

    _method_registry[cls.name] = cls


def get_method(method_name: str) -> MethodCls:
    """Get a Method class based on its name."""
    if method_name not in _method_registry:
        raise KeyError(
            f'No Method with name "{method_name}" found!'
            " Check that the name is correctly spelled and that the module containing"
            " the class is being imported."
        )
    return _method_registry[method_name]


def get_methods(
    names: Collection[str] | None = None,
) -> Collection[MethodCls] | None:
    """Get a collection (list, tuple or set) of Method classes based on their
    names."""

    if names is None:
        return None

    if isinstance(names, list):
        return [get_method(name) for name in names]
    elif isinstance(names, tuple):
        return tuple(get_method(name) for name in names)
    elif isinstance(names, set):
        return set(get_method(name) for name in names)

    raise TypeError("`names` must be a list, tuple or set")


def get_methods_for_mode(
    modename: ModeName,
) -> List[MethodCls]:
    """Get the Method classes belonging to a Mode; Methods with
    Method.mode = `modename`.

    Parameters
    ----------
    modename: str | ModeName
        The name of the Mode from which to select the Methods.

    Returns
    -------
    methods: list[MethodCls]
        The Method classes for the Mode.
    """
    methods = []
    for method_cls in _method_registry.values():
        if method_cls.mode != modename:
            continue
        methods.append(method_cls)

    return methods
