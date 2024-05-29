"""The Freedesktop.org related methods"""

from __future__ import annotations

import os
import typing

from wakepy.core import (
    BusType,
    DBusAddress,
    DBusMethod,
    DBusMethodCall,
    Method,
    ModeName,
    PlatformName,
)

if typing.TYPE_CHECKING:
    from typing import Optional


class FreedesktopScreenSaverInhibit(Method):
    """Method using org.freedesktop.ScreenSaver D-Bus API

    https://people.freedesktop.org/~hadess/idle-inhibition-spec/re01.html
    """

    name = "org.freedesktop.ScreenSaver"
    mode_name = ModeName.KEEP_PRESENTING

    screen_saver = DBusAddress(
        bus=BusType.SESSION,
        service="org.freedesktop.ScreenSaver",
        path="/org/freedesktop/ScreenSaver",
        interface="org.freedesktop.ScreenSaver",
    )

    method_inhibit = DBusMethod(
        name="Inhibit",
        signature="ss",
        params=("application_name", "reason_for_inhibit"),
        output_signature="u",
        output_params=("cookie",),
    ).of(screen_saver)

    method_uninhibit = DBusMethod(
        name="UnInhibit",
        signature="u",
        params=("cookie",),
    ).of(screen_saver)

    supported_platforms = (PlatformName.LINUX,)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.inhibit_cookie: Optional[int] = None

    def enter_mode(self) -> None:
        call = DBusMethodCall(
            method=self.method_inhibit,
            args=dict(
                application_name="wakepy",
                reason_for_inhibit="wakelock active",
            ),
        )

        retval = self.process_dbus_call(call)
        if retval is None:
            raise RuntimeError(
                "Could not get inhibit cookie from org.freedesktop.ScreenSaver"
            )
        self.inhibit_cookie = retval[0]

    def exit_mode(self) -> None:
        if self.inhibit_cookie is None:
            # Nothing to exit from.
            return

        call = DBusMethodCall(
            method=self.method_uninhibit,
            args=dict(cookie=self.inhibit_cookie),
        )
        self.process_dbus_call(call)
        self.inhibit_cookie = None


class FreedesktopPowerManagementInhibit(Method):
    """Method using org.freedesktop.PowerManagement D-Bus API

    According to [1] and [2] this might be obsolete. The spec itself can be
    read in the internet arhives[3]. Part of the spec (v0.2.0) copied here for
    convenience:

    DBUS Interface:     org.freedesktop.PowerManagement.Inhibit
    DBUS Path:          /org/freedesktop/PowerManagement/Inhibit

    When the power manager detects an idle session and system, it can perform a
    system suspend or hibernate, known as an idle sleep action. We can prevent
    the session power manager daemon from doing this action using the inhibit
    interface.

    An automatic inhibit should be taken by the file manager if there is a slow
    network copy that will take many minutes to complete.

    A cookie is a randomly assigned 32bit unsigned integer used to identify the
    inhibit. It is required as the same application may want to call inhibit
    multiple times, without managing the inhibit calls itself.

    Name        Input               Output      Error               Description
    -------     ------------------  -------     ------              -----------
    Inhibit     string application  uint cookie PermissionDenied    [D1]
                string reason
    UnInhibit   uint cookie                     CookieNotFound      [D2]
    HasInhibit  bool has_inhibit                                    [D3]

    [D1] Inhibits the computer from performing an idle sleep action. Useful if
    you want to do an operation of long duration without the computer
    suspending. Reason and application should be translated strings where
    possible.

    [D2] Allows the computer to perform the idle sleep or user action if the
    number of inhibit calls is zero. If there are multiple cookies outstanding,
    clearing one cookie does not allow the action to happen. If the program
    holding the cookie exits from the session bus without calling UnInhibit()
    then it is automatically removed.

    [D3] Returns false if we have no valid inhibits. This will return true if
    the number of inhibit cookies is greater than zero.

    [1] https://code.videolan.org/videolan/vlc/-/issues/25785
    [2] https://www.freedesktop.org/wiki/Specifications/power-management-spec/
    [3] https://web.archive.org/web/20090417010057/http://people.freedesktop.org/~hughsient/temp/power-management-spec-0.2.html

    """

    name = "org.freedesktop.PowerManagement"
    mode_name = ModeName.KEEP_RUNNING

    screen_saver = DBusAddress(
        bus=BusType.SESSION,
        service="org.freedesktop.PowerManagement",
        path="/org/freedesktop/PowerManagement/Inhibit",
        interface="org.freedesktop.PowerManagement.Inhibit",
    )

    method_inhibit = DBusMethod(
        name="Inhibit",
        signature="ss",
        params=("application_name", "reason_for_inhibit"),
        output_signature="u",
        output_params=("cookie",),
    ).of(screen_saver)

    method_uninhibit = DBusMethod(
        name="UnInhibit",
        signature="u",
        params=("cookie",),
    ).of(screen_saver)

    supported_platforms = (PlatformName.LINUX,)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.inhibit_cookie: Optional[int] = None

    def caniuse(self) -> bool | None | str:

        XDG_CURRENT_DESKTOP = "XDG_CURRENT_DESKTOP"

        if XDG_CURRENT_DESKTOP not in os.environ:
            raise RuntimeError(f"{XDG_CURRENT_DESKTOP} not set!")

        if os.environ[XDG_CURRENT_DESKTOP] != "KDE":
            # Could in theory support also other DEs, but every DE may behave
            # differently with this.

            raise RuntimeError(
                (
                    f"{self.name} only supports KDE. {XDG_CURRENT_DESKTOP} "
                    f"was set to {os.environ[XDG_CURRENT_DESKTOP]}"
                )
            )
        return True

    def enter_mode(self) -> None:
        call = DBusMethodCall(
            method=self.method_inhibit,
            args=dict(
                application_name="wakepy",
                reason_for_inhibit="wakelock active",
            ),
        )

        retval = self.process_dbus_call(call)
        if retval is None:
            raise RuntimeError(
                "Could not get inhibit cookie from org.freedesktop.PowerManagement"
            )
        self.inhibit_cookie = retval[0]

    def exit_mode(self) -> None:
        if self.inhibit_cookie is None:
            # Nothing to exit from.
            return

        call = DBusMethodCall(
            method=self.method_uninhibit,
            args=dict(cookie=self.inhibit_cookie),
        )
        self.process_dbus_call(call)
        self.inhibit_cookie = None
