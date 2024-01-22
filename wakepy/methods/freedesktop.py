"""The Freedesktop.org related methods"""

from typing import Optional

from wakepy.core import (
    BusType,
    DbusAddress,
    DbusMethod,
    DbusMethodCall,
    Method,
    ModeName,
    PlatformName,
)


class FreedesktopScreenSaverInhibit(Method):
    """Method using org.freedesktop.ScreenSaver D-Bus API

    https://people.freedesktop.org/~hadess/idle-inhibition-spec/re01.html
    """

    name = "org.freedesktop.ScreenSaver"
    mode = ModeName.KEEP_PRESENTING

    screen_saver = DbusAddress(
        bus=BusType.SESSION,
        service="org.freedesktop.ScreenSaver",
        path="/org/freedesktop/ScreenSaver",
        interface="org.freedesktop.ScreenSaver",
    )

    method_inhibit = DbusMethod(
        name="Inhibit",
        signature="ss",
        params=("application_name", "reason_for_inhibit"),
        output_signature="u",
        output_params=("cookie",),
    ).of(screen_saver)

    method_uninhibit = DbusMethod(
        name="Uninhibit",
        signature="u",
        params=("cookie",),
    ).of(screen_saver)

    supported_platforms = (PlatformName.LINUX,)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inhibit_cookie: Optional[int] = None

    def enter_mode(self):
        call = DbusMethodCall(
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

    def exit_mode(self):
        if self.inhibit_cookie is None:
            # Nothing to exit from.
            return

        call = DbusMethodCall(
            method=self.method_uninhibit,
            args=dict(cookie=self.inhibit_cookie),
        )
        self.process_dbus_call(call)
        self.inhibit_cookie = None
