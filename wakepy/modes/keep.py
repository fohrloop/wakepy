from ..core.mode import Mode
from ..methods.gnome import GnomeSessionManagerNoIdle, GnomeSessionManagerNoSuspend


class KeepRunning(Mode):
    methods = [
        GnomeSessionManagerNoSuspend,
    ]


class KeepPresenting(Mode):
    methods = [
        GnomeSessionManagerNoIdle,
    ]


running = KeepRunning
presenting = KeepPresenting
