from __future__ import annotations

import typing
from abc import ABC

from .activationresult import ActivationResult
from .activationmanager import ModeActivationManager

if typing.TYPE_CHECKING:
    from types import TracebackType
    from typing import Optional, Type, Tuple

    from .method import Method
    from .dbus import DbusAdapter, DbusAdapterTypeSeq


class ModeExit(Exception):
    """This can be used to exit from any wakepy mode with block. Just raise it
    within any with block which is a wakepy mode, and no code below it will
    be executed.

    Example
    -------
    ```
    with keep.running() as k:
        if not k.success:
            print('failure')
            raise ModeExit
        print('success')
    ```

    This will print just "failure" in case entering a Mode did not succeed and
    just "success" in case it did succeed (never both).
    """


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
        return self.manager.activate(methods=self.methods)

    def __exit__(
        self,
        *exc_info: Tuple[
            Optional[Type[BaseException]],
            Optional[BaseException],
            Optional[TracebackType],
        ],
    ) -> bool:
        """Called when exiting the with block.

        If with block completed normally, called with (None, None, None)
        If with block had an exception, called with (exc_type, exc_value,
        traceback), which is the same as *sys.exc_info

        Will swallow any ModeExit exception. Other exceptions will be
        re-raised.
        """

        self.manager.deactivate()

        exception = exc_info[1]
        if exception is None or isinstance(exception, ModeExit):
            return True

        # Other types of exceptions are not handled; ignoring them here and
        # returning False will tell python to re-raise the exception. Can't
        # return None as type-checkers will mark code after with block
        # unreachable
        return False
