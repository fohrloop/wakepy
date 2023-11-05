from __future__ import annotations

import typing
from queue import Queue

from .activationresult import ActivationResult
from .modeactivator import ModeWorkerThread

if typing.TYPE_CHECKING:
    from typing import List, Optional, Type

    from .dbus import DbusAdapter, DbusAdapterSeq
    from .method import Method


class ModeActivationManager:
    def __init__(
        self,
        prioritize: Optional[List[Type[Method]]] = None,
        dbus_adapter: DbusAdapter | DbusAdapterSeq | None = None,
    ):
        """
        Parameters
        ---------
        dbus_adapter
            Determines, which Dbus library / implementation is to be used, if
            Dbus-based methods are to be used with a mode. You may use this to
            use a custom DBus implementation. Wakepy is in no means tightly
            coupled to any specific python dbus package.
        """

        self._prioritize = prioritize
        self._thread: ModeWorkerThread | None = None
        self._queue_in: Queue | None = None
        self._queue_out: Queue | None = None
        self.results: ActivationResult | None = None

    def activate(self, methods: List[Type[Method]]) -> ActivationResult:
        # The actual mode activation happens in a separate thread
        self._queue_in = Queue()
        self._queue_out = Queue()
        self._thread = ModeWorkerThread(
            methods, queue_in=self._queue_out, queue_out=self._queue_in
        )
        self._thread.start()

        self.results = ActivationResult(
            queue_thread=self._queue_in, candidate_methods=methods
        )
        return self.results

    def deactivate(self):
        """TODO: Implement this."""
