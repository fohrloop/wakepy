from __future__ import annotations

import typing
from abc import ABC

from .activationresult import ActivationResult
from .modemanager import ModeActivationManager

if typing.TYPE_CHECKING:
    from types import TracebackType
    from typing import Optional, Type

    from .method import Method
    from .dbus import DbusAdapter, DbusAdapterTypeSeq


class ModeManagerNotSetError(RuntimeError):
    ...


class Mode(ABC):
    """A mode is something that is entered into, kept, and exited from. Modes
    are implemented as context managers, and user code (inside the with
    statement body) runs during the "keeping" the mode. The "keeping" has
    a possibility to run a heartbeat.

    Purpose of Mode:
    * Provide the main API of wakepy for the user
    * Provide __enter__ for fulfilling the context manager protocol
    * Provide __exit__ for fulfilling the context manager protocol
    * Provide easy way to define list of Methods to be used for entering a mode

    Attributes
    ----------
    methods: list[Type[Method]]
        The list of methods associated for this mode.
    manager: ModeActivationManager
        The manager which lives in the main thread and talks to the
        ModeActivator using queues. This is responsive for activating and
        deactivating a mode.
    """

    _manager_class: Type[ModeActivationManager] = ModeActivationManager

    def __init__(
        self,
        methods: list[Type[Method]],
        dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None,
    ):
        """Initialize a MOde using Methods.

        This is also where the ModeActivationManager settings, such as the dbus
        adapter to be used, are defined.

        Parameters
        ----------
        methods:
            The list of Methods to be used for activating this Mode.
        dbus_adapter:
            For using a custom dbus-adapter. Optional.
        """
        self.methods = methods
        self.manager: ModeActivationManager = self._manager_class(
            dbus_adapter=dbus_adapter
        )

    def __enter__(self) -> ActivationResult:
        if self.manager is None:
            self.__call__()

        return self.manager.activate(methods=self.methods)

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        self.manager.deactivate()

        if not exc_value:
            return True