import enum
from abc import ABC, abstractmethod
from typing import Optional

from wakepy.core import BusType, DbusAddress, DbusMethod, DbusMethodCall
from wakepy.core.method import Method, SystemName


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

    session_manager = DbusAddress(
        bus=BusType.SESSION,
        service="org.gnome.SessionManager",
        path="org/gnome/SessionManager",
        interface="org.gnome.SessionManager",
    )

    method_isinhibited = DbusMethod(
        name="IsInhibited",
        signature="u",
        params=("flags",),
        output_signature="b",
        output_params=("is_inhibited",),
    ).of(session_manager)

    method_inhibit = DbusMethod(
        name="Inhibit",
        signature="susu",
        params=("app_id", "toplevel_xid", "reason", "flags"),
        output_signature="u",
        output_params=("inhibit_cookie",),
    ).of(session_manager)

    method_uninhibit = DbusMethod(
        name="UnInhibit",
        signature="u",
        params=("inhibit_cookie",),
    ).of(session_manager)

    supported_systems = (SystemName.LINUX,)

    @property
    @abstractmethod
    def flags(self) -> GnomeFlag:
        ...

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inhibit_cookie: Optional[int] = None

    def enter_mode(self):
        call = DbusMethodCall(
            method=self.method_inhibit,
            args=dict(
                app_id="wakepy",
                toplevel_xid=42,  # The value does not seem to matter.
                reason="wakelock active",
                flags=self.flags,
            ),
        )
        self.inhibit_cookie = self.process_call(call)

    def exit_mode(self):
        if self.inhibit_cookie is None:
            raise ValueError("Cannot exit before entering")

        call = DbusMethodCall(
            method=self.method_uninhibit,
            args=dict(inhibit_cookie=self.inhibit_cookie),
        )
        self.process_call(call)
        self.inhibit_cookie = None


class GnomeSessionManagerNoSuspend(_GnomeSessionManager):
    name = "org.gnome.SessionManager:Inhibit:Suspend"
    flags = GnomeFlag.INHIBIT_SUSPEND


class GnomeSessionManagerNoIdle(_GnomeSessionManager):
    name = "org.gnome.SessionManager:Inhibit:Idle"
    flags = GnomeFlag.INHIBIT_IDLE
