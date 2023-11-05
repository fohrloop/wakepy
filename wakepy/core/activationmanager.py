from __future__ import annotations

import typing
from queue import Queue
from threading import Thread

from .activationresult import ActivationResult
from .modeactivator import activate

if typing.TYPE_CHECKING:
    from typing import List, Optional, Type

    from .dbus import DbusAdapter, DbusAdapterTypeSeq
    from .method import Method


class ModeActivationManager:
    """Mode Activation Manager

    Purpose:
    (1) Manage activation of a mode using a collection of methods. Do this by
      creating a separate thread for the mode activation, and communicate with
      that thread using Queues.
    (2) Form an ActivationResult from the result of the activation process and
      provide it to the user.

    The manager itself is always running in the "main" thread; The thread where
    a wakepy mode is entered in.
    """

    def __init__(
        self,
        dbus_adapter: Type[DbusAdapter] | DbusAdapterTypeSeq | None = None,
    ):
        """
        Parameters
        ---------
        dbus_adapter:
            Determines, which Dbus library / implementation is to be used, if
            Dbus-based methods are to be used with a mode. You may use this to
            use a custom DBus implementation. Wakepy is in no means tightly
            coupled to any specific python dbus package.
        """
        self._dbus_adapter = dbus_adapter
        self._activation_thread: Thread | None = None
        self._queue_in: Queue | None = None
        self._queue_out: Queue | None = None
        self.results: ActivationResult | None = None

    def activate(
        self,
        methods: List[Type[Method]],
        prioritize: Optional[List[Type[Method]]] = None,
    ) -> ActivationResult:
        """Activate a mode defined by the methods.

        Parameters
        -----------
        methods:
            The list of Methods to be used for activating this Mode.
        prioritize:
            If given a list of Methods (classes), this list will be used to
            order the returned Methods in the order given in `prioritize`. Any
            Method in `prioritize` but not in the `methods` list will be
            disregarded. Any method in `methods` but not in `prioritize`, will
            be placed in the output list just after all prioritized methods, in
            same order as in the original `methods`.
        """

        # Used for communicating to the mode activation thread
        self._queue_in = Queue()
        self._queue_out = Queue()

        self._activation_thread = Thread(
            target=activate,
            kwargs=dict(
                methods=methods,
                prioritize=prioritize,
                queue_in=self._queue_out,
                queue_out=self._queue_in,
                dbus_adapter=self._dbus_adapter,
            ),
        )
        self._activation_thread.start()

        # The results. These need a reference to the manager, as all results
        # are lazy-loaded, and the ActivationResult should not need to know
        # anything about threads or queues. If it has a question, it will ask
        # it from the manager.
        self.results = ActivationResult(manager=self)
        return self.results

    def deactivate(self):
        """TODO: Implement this."""
        self._queue_out.put("EXIT")
        self._activation_thread.join()
