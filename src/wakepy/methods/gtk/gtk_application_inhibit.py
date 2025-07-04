from __future__ import annotations

import enum
import typing
from abc import ABC, abstractmethod

from wakepy.core import Method, ModeName, PlatformType
from wakepy.pyinhibitor import get_inhibitor

if typing.TYPE_CHECKING:
    from typing import Optional


class GtkIhibitFlag(enum.IntFlag):
    """The ApplicationInhibitFlags from
    https://docs.gtk.org/gtk4/flags.ApplicationInhibitFlags.html
    """

    # Inhibit suspending the session or computer
    INHIBIT_SUSPEND = 4
    # Inhibit the session being marked as idle (and possibly locked).
    INHIBIT_IDLE = 8


class _GtkApplicationInhibit(Method, ABC):
    """Method using the gtk_application_inhibit().

    https://docs.gtk.org/gtk4/method.Application.inhibit.html

    Works on GTK 3 and 4.
    """

    supported_platforms = (PlatformType.UNIX_LIKE_FOSS,)
    inhibitor_module = "wakepy.methods.gtk.inhibitor"

    @property
    @abstractmethod
    def flags(self) -> GtkIhibitFlag: ...

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.inhibit_cookie: Optional[int] = None

    def enter_mode(self) -> None:
        self.inhibitor = get_inhibitor(self.inhibitor_module)
        # TODO: use flags
        self.inhibitor.start()

    def exit_mode(self) -> None:
        self.inhibitor.stop()


class GtkApplicationInhibitNoSuspend(_GtkApplicationInhibit):
    name = "gtk_application_inhibit"
    mode_name = ModeName.KEEP_RUNNING
    flags = GtkIhibitFlag.INHIBIT_SUSPEND


class GtkApplicationInhibitNoIdle(_GtkApplicationInhibit):
    name = "gtk_application_inhibit"
    mode_name = ModeName.KEEP_PRESENTING
    flags = GtkIhibitFlag.INHIBIT_IDLE | GtkIhibitFlag.INHIBIT_SUSPEND
