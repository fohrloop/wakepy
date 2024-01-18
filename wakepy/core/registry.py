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
    from typing import Optional

    T = TypeVar("T")

    Collection = Union[List[T], Tuple[T, ...], Set[T]]
    MethodDict = dict[str, MethodCls]
    MethodRegistry = dict[str, MethodDict]

_method_registry: MethodRegistry = dict()
"""A name -> Method class mapping. Updated automatically; when python loads
a module with a subclass of Method, the Method class is added to this registry.
"""


class MethodRegistryError(RuntimeError):
    """Any error which is related to the method registry"""


def register_method(method_class: Type[Method]):
    """Registers a subclass of Method to the method registry"""

    if method_class.name is None:
        # Methods without a name will not be registered
        return

    method_dict: MethodDict = _method_registry.get(method_class.mode, dict())

    if method_class.name in method_dict:
        if method_dict[method_class.name] is not method_class:
            # The same class registered with different name -> raise Exception
            raise MethodRegistryError(
                f'Duplicate Method name "{method_class.name}": '
                f"{method_class.__qualname__} "
                "(already registered to "
                f"{method_dict[method_class.name].__qualname__})"
            )
        else:
            # The same class registered with same name. No action required.
            return

    # Register a new method class
    method_dict[method_class.name] = method_class
    _method_registry.setdefault(method_class.mode, method_dict)


def get_method(method_name: str, mode: Optional[ModeName] = None) -> MethodCls:
    """Get a Method class based on its name and optionally the mode.

    Parameters
    ----------
    method_name: str
        The name of the wakepy.Method. The method must be registered which
        means that the module containing the subclass definition must have
        been imported.
    mode: str | ModeName | None
        If the method_name is registered to methods belonging to multiple
        Modes, you must provide the mode name, to make the selection
        unambiguous. Typical mode names are "keep.running" and
        "keep.presenting".

    Raises
    ------
    ValueError
        Raised if the method does not exist, or if the method exists in
        multiple modes, but the mode was not provided as argument to make the
        selection unambiguous.

    """
    method_dict = _method_registry.get(mode, dict())

    if method_name not in method_dict:
        raise ValueError(
            f'No Method with name "{method_name}" found!'
            " Check that the name is correctly spelled and that the module containing"
            " the class is being imported."
        )
    return method_dict[method_name]


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
