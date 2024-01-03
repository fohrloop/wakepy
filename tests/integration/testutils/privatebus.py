import subprocess


class PrivateSessionBus:
    """A real, private message bus (dbus-daemon) instance which can be used
    to test dbus adapters. You can see the bus running with

    $ ps -x | grep dbus-daemon | grep -v grep | grep dbus-daemon

    It is listed as `PrivateSessionBus._start_cmd`  (e.g. "dbus-daemon
    --session --print-address")

    See: https://dbus.freedesktop.org/doc/dbus-daemon.1.html
    """

    _start_cmd = "dbus-daemon --session --print-address"

    def __init__(self):
        self.p: subprocess.Popen | None = None
        self.bus_address: str | None = None

    def start(self) -> str:
        if self.p:
            raise Exception("dbus-daemon already running!")

        self.p = subprocess.Popen(
            self._start_cmd.split(),
            stdout=subprocess.PIPE,
            shell=False,
            env={"DBUS_VERBOSE": "1"},
        )

        self.bus_address = self.p.stdout.readline().decode("utf-8").strip()
        return self.bus_address

    def stop(self):
        self.p.terminate()
        self.p = None
        self.bus_address = None
