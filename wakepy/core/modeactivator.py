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
