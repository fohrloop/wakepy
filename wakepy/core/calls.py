from __future__ import annotations

import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from typing import Any, List, Tuple

    from wakepy.core.dbus import DbusMethod


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
