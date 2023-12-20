from __future__ import annotations

import typing
from queue import Empty, Queue
from threading import Thread

from . import CURRENT_PLATFORM, PlatformName
from .constants import ControlMsg, WorkerThreadMsgType

if typing.TYPE_CHECKING:
    from typing import List, Optional, Type

    from .dbus import DbusAdapter, DbusAdapterTypeSeq
    from .method import Method


def activate(
    methods: List[Type[Method]],
    queue_in: Queue,
    queue_out: Queue,
    prioritize: Optional[List[Type[Method]]] = None,
    dbus_adapter: DbusAdapter | DbusAdapterTypeSeq | None = None,
):
    """dummy function
    TODO: Replace with real implementation"""


def sort_methods_by_priority(
    methods: List[Type[Method]],
    prioritize: Optional[List[Type[Method]]] = None,
) -> List[Type[Method]]:
    """Sort `methods` based on `prioritize`.

    Parameters
    ----------
    prioritize:
        If given a list of Methods (classes), this list will be used to
        order the returned Methods in the order given in `prioritize`. Any
        Method in `prioritize` but not in the `methods` list will be
        disregarded. Any method in `methods` but not in `prioritize`, will be
        placed in the output list just after all prioritized methods, in same
        order as in the original `methods`.
    """

    if not prioritize:
        return methods

    sorted_methods = sorted(
        methods,
        key=lambda method: prioritize.index(method)
        if method in prioritize
        else float("inf"),
    )
    return sorted_methods


# TODO: Remove / merge this to existing code.
class ModeWorkerThread(Thread):
    def __init__(
        self,
        methods: List[Method],
        queue_in: Queue,
        queue_out: Queue,
        platform: PlatformName = CURRENT_PLATFORM,
        *args,
        **kwargs,
    ):
        super().__init__(*args, name="wakepy-mode-manager", **kwargs)
        self.methods = methods
        self.platform = platform
        self.queue_in = queue_in
        self.queue_out = queue_out

    def run(self):
        try:
            candidate_methods = self.check_suitability(self.methods)
            self.try_activate_mode(candidate_methods)

            self.queue_out.put((WorkerThreadMsgType.OK, None))
        except Exception as exc:
            self.queue_out.put((WorkerThreadMsgType.EXCEPTION, exc))

    def check_suitability(
        self,
        methods: List[Method],
    ) -> List[Method]:
        candidate_methods = []
        for method in methods:
            self.check_input_queue()
            method.set_suitability(platform=self.platform)
            candidate_methods.append(method)
        return candidate_methods

    def try_activate_mode(
        self,
        methods: List[Method],
    ) -> List[Method]:
        """
        Activate a mode by trying the methods in the input list.

        Returns
        --------
        successful_methods
            List of methods which were successful.

        Raises
        ------
        ExitModeError in the rare case where (1) enter_mode() and heartbeat()
        and exit_more() are all implemented and (2) enter_mode() succeeds and
        (3) heartbeat raises exception and (4) exit_mode() raises exception.

        MethodError in the (erroreously implemented) case where (1)
        enter_mode() and heartbeat() are both not implemented, and no successful
        activation is possible.
        """

        succesful_methods = []
        for method in methods:
            self.check_input_queue()
            success = method.activate_the_mode()
            if success:
                succesful_methods.append(method)
        return succesful_methods

    def check_input_queue(self):
        try:
            item = self.queue_in.get(block=False)
        except Empty:
            return None
        self._handle_input_queue_item(item)

    def _handle_input_queue_item(self, item):
        if item == ControlMsg.TERMINATE:
            self.exit_modes()
        raise ValueError(f'Queue input not understood: "{item}"')
