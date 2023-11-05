from __future__ import annotations

import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from typing import Any, List, Tuple

    from .dbus import DbusAdapter, DbusAdapterSeq, DbusMethod


class Call:
    """Base Call class. Needed at least for type checking and for making
    talking about how everything works easier

    Modes use Methods which create Calls, which are then invoked by an Adapter.
    For example, DbusMethodCalls are invoked by DbusAdapters.
    """


@dataclass
class DbusMethodCall(Call):
    method: DbusMethod
    """The method which is the target of the call. Must be completely defined.
    """

    args: dict[str, Any] | Tuple[Any, ...] | List[Any]

    def __post_init__(self):
        if not self.method.completely_defined():
            raise ValueError(
                f"{self.__class__.__name__} requires completely defined DBusMethod!"
            )


# TODO: Define a Caller class


def _to_tuple_of_dbus_adapter(
    dbus_adapter: DbusAdapter | DbusAdapterSeq | None,
) -> tuple[DbusAdapter, ...] | None:
    """Makes sure that dbus_adapter is a tuple of DbusAdapter instances."""
    if not dbus_adapter:
        return None

    elif isinstance(dbus_adapter, DbusAdapter):
        return (dbus_adapter,)

    if isinstance(dbus_adapter, (list, tuple)):
        if not all(isinstance(a, DbusAdapter) for a in dbus_adapter):
            raise ValueError("dbus_adapter can only consist of DbusAdapters!")
        return tuple(dbus_adapter)

    raise ValueError("dbus_adapter type not understood")


def get_default_dbus_adapter() -> tuple[DbusAdapter, ...]:
    try:
        from wakepy.io.dbus.jeepney import JeepneyDbusAdapter
    except ImportError:
        return tuple()
    return (JeepneyDbusAdapter(),)
