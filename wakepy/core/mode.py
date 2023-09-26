from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from queue import Empty, Queue
from threading import Thread

from . import CURRENT_SYSTEM, SystemName
from .activationresult import ActivationResult
from .dbus import DbusAdapter
from .definitions import ControlMsg, WorkerThreadMsgType
from .method import Suitability

if typing.TYPE_CHECKING:
    from types import TracebackType
    from typing import Iterable, List, Optional, Tuple, Type

    from .method import Method

    DbusAdapterSeq = typing.Union[List[DbusAdapter], Tuple[DbusAdapter]]


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


class ModeWorkerThread(Thread):
    def __init__(
        self,
        methods: List[Method],
        queue_in: Queue,
        queue_out: Queue,
        system: SystemName = CURRENT_SYSTEM,
        *args,
        **kwargs,
    ):
        super().__init__(*args, name="wakepy-mode-manager", **kwargs)
        self.methods = methods
        self.system = system
        self.queue_in = queue_in
        self.queue_out = queue_out

    def run(self):
        try:
            candidate_methods = self.check_suitability(self.methods)
            succesful_methods = self.try_activate_mode(candidate_methods)

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
            method.set_suitability(system=self.system)
            if method.suitability == Suitability.UNSUITABLE:
                continue
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


class Mode(ABC):
    """A mode is something that is entered into, kept, and exited from. Modes
    are implemented as context managers, and user code (inside the with
    statement body) runs during the "keeping" the mode. The "keeping" has
    a possibility to run a heartbeat.

    Purpose of Mode:
    * Provide __enter__ for fulfilling the context manager protocol
    * Provide __exit__ for fulfilling the context manager protocol
    * Provide easy way to define list of Methods to be used for entering a mode
    (in subclasses)

    Attributes
    ----------
    methods:
        The list of methods associated for this mode. Usually defined as a
        class level attribute.

    """

    @property
    @abstractmethod
    def methods(self) -> Iterable[Type[Method]]:
        ...

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
        self._dbus_adapters: Tuple[DbusAdapter, ...] = (
            _to_tuple_of_dbus_adapter(dbus_adapter) or get_default_dbus_adapter()
        )
        self._prioritize = prioritize
        self._thread: ModeWorkerThread | None = None
        self._queue_in: Queue | None = None
        self._queue_out: Queue | None = None
        self.results: ActivationResult | None = None

    def __enter__(self) -> ActivationResult:
        methods = self._get_methods()

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

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        # TODO: do exit in the thread.
        active_methods = self.results.used_methods
        for method in active_methods:
            method.exit_mode()

        if not exc_value:
            return True

    def _get_method_classes(self) -> List[Type[Method]]:
        return sort_methods_by_priority(self.methods, prioritize=self._prioritize)

    def _get_methods(self) -> List[Method]:
        return [
            method_cls(dbus_adapters=self._dbus_adapters)
            for method_cls in self._get_method_classes()
        ]
