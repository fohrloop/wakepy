from __future__ import annotations

import enum
import typing
from abc import ABC, abstractmethod

from wakepy.core import (
    BusType,
    DBusAddress,
    DBusMethod,
    DBusMethodCall,
    Method,
    ModeName,
    PlatformType,
)

if typing.TYPE_CHECKING:
    from typing import Optional


class GnomeFlag(enum.IntFlag):
    INHIBIT_LOG_OUT = 1
    INHIBIT_SWITCH_USER = 2
    # Inhibit suspending the session or computer
    INHIBIT_SUSPEND = 4
    # Inhibit the session being marked as idle
    INHIBIT_IDLE = 8
    # Inhibit auto-mounting removable media for the session
    INHIBIT_AUTO_MOUNT_MEDIA = 16


class _GnomeSessionManager(Method, ABC):
    """Method using org.gnome.SessionManager D-Bus API

    https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html#org.gnome.SessionManager.Inhibit
    """

    session_manager = DBusAddress(
        bus=BusType.SESSION,
        service="org.gnome.SessionManager",
        path="/org/gnome/SessionManager",
        interface="org.gnome.SessionManager",
    )

    method_inhibit = DBusMethod(
        name="Inhibit",
        signature="susu",
        params=("app_id", "toplevel_xid", "reason", "flags"),
        output_signature="u",
        output_params=("inhibit_cookie",),
    ).of(session_manager)

    method_uninhibit = DBusMethod(
        name="Uninhibit",
        signature="u",
        params=("inhibit_cookie",),
    ).of(session_manager)

    supported_platforms = (PlatformType.UNIX_LIKE_FOSS,)

    @property
    @abstractmethod
    def flags(self) -> GnomeFlag: ...

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.inhibit_cookie: Optional[int] = None

    def enter_mode(self) -> None:
        call = DBusMethodCall(
            method=self.method_inhibit,
            args=dict(
                app_id="wakepy",
                toplevel_xid=42,  # The value does not seem to matter.
                reason="wakelock active",
                flags=int(self.flags),
            ),
        )

        retval = self.process_dbus_call(call)
        if retval is None:
            raise RuntimeError(
                "Could not get inhibit cookie from org.gnome.SessionManager"
            )
        self.inhibit_cookie = retval[0]

    def exit_mode(self) -> None:
        if self.inhibit_cookie is None:
            # Nothing to exit from.
            return

        call = DBusMethodCall(
            method=self.method_uninhibit,
            args=dict(inhibit_cookie=self.inhibit_cookie),
        )
        self.process_dbus_call(call)
        self.inhibit_cookie = None


class GnomeSessionManagerNoSuspend(_GnomeSessionManager):
    name = "org.gnome.SessionManager"
    mode_name = ModeName.KEEP_RUNNING
    flags = GnomeFlag.INHIBIT_SUSPEND


class GnomeSessionManagerNoIdle(_GnomeSessionManager):
    name = "org.gnome.SessionManager"
    mode_name = ModeName.KEEP_PRESENTING
    flags = GnomeFlag.INHIBIT_IDLE
