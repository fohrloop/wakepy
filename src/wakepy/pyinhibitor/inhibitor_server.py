from __future__ import annotations

import importlib.util
import sys
import typing
import warnings
from pathlib import Path
from socket import AF_UNIX, SOCK_STREAM, socket

if sys.version_info < (3, 8):  # pragma: no-cover-if-py-gte-38
    from typing_extensions import Protocol
else:  # pragma: no-cover-if-py-lt-38
    from typing import Protocol

if typing.TYPE_CHECKING:
    from typing import Type


class Inhibitor(Protocol):
    """The Inhibitor protocol. An inhibitor module should provide a class
    called Inhibitor which implements this protocol."""

    def start(self, *args) -> None: ...
    def stop(self) -> None: ...


CLIENT_CONNECTION_TIMEOUT = 60
"""Time to wait (seconds) for the client to connect to the server."""
CLIENT_MESSAGE_TIMEOUT = 1
"""Time to wait (seconds) for each message from the client."""


class InhibitorServer:
    """A very simple class for inhibiting suspend/idle.

    Communicates with a main process using a Unix domain socket.

    What happens when run() is called:
    1. When the process starts, inhibit() is called. If it succeeds, this
       process sends "INHIBIT_OK". If it fails, this process sends
       "INHIBIT_ERROR:{errortext}" and exits.
    2. This process waits indefinitely for a "QUIT" message.
    3. When "QUIT" (or empty string) is received, uninhibit() is called. If it
        succeeds, this process sends "UNINHIBIT_OK". If it fails, this process
        sends "UNINHIBIT_ERROR". Then, this process exits.
    """

    def __init__(self):
        self._inhibitor: Inhibitor | None = None

    def run(self, socket_path: str, inhibitor_module: str, *inhibit_args) -> None:
        """Inhibit the system using inhibitor_module and wait for a quit
        message at socket_path.

        Parameters
        ----------
        socket_path : str
            The path to the Unix domain socket which is used for communication.
        inhibitor_module : str
            The python module that contains the Inhibitor class
        inhibit_args:
            Any arguments to the Inhibitor.start() method.
        """
        server_socket = socket(AF_UNIX, SOCK_STREAM)
        Path(socket_path).expanduser().unlink(missing_ok=True)
        server_socket.bind(socket_path)

        try:
            self._run(server_socket, inhibitor_module, *inhibit_args)
        finally:
            server_socket.close()

    def _run(self, server_socket: socket, inhibitor_module: str, *inhibit_args) -> None:
        server_socket.listen(1)  # Only allow 1 connection at a time
        client_socket = self._get_client_socket(server_socket)
        client_socket.settimeout(CLIENT_MESSAGE_TIMEOUT)

        try:
            self.inhibit(inhibitor_module, *inhibit_args)
            self.send_message(client_socket, "INHIBIT_OK")
        except Exception as error:
            self.send_message(client_socket, f"INHIBIT_ERROR:{error}")
            sys.exit(0)

        while True:
            # Called every `CLIENT_MESSAGE_TIMEOUT` seconds.
            should_quit = self.check_for_quit_message(client_socket)
            if should_quit:
                break

        try:
            self.uninhibit()
            self.send_message(client_socket, "UNINHIBIT_OK")
        except Exception as error:
            self.send_message(client_socket, f"UNINHIBIT_ERROR:{error}")
            sys.exit(0)

    @staticmethod
    def _get_client_socket(server_socket: socket) -> socket:
        server_socket.settimeout(CLIENT_CONNECTION_TIMEOUT)

        try:
            client_socket, _ = server_socket.accept()
        except TimeoutError as e:
            raise TimeoutError(
                f"Client did not connect within {CLIENT_CONNECTION_TIMEOUT} seconds."
            ) from e
        except KeyboardInterrupt:
            print("Interrupted manually. Exiting.")
            sys.exit(0)

        return client_socket

    def inhibit(self, inhibitor_module: str, *inhibit_args) -> None:
        """Inhibit using the Inhibitor class in the given `inhibitor_module`.
        In case the operation fails, raises a RuntimeError."""
        inhibitor_class = self.get_inhibitor_class(inhibitor_module)
        self._inhibitor = inhibitor_class()
        self._inhibitor.start(*inhibit_args)

    @staticmethod
    def get_inhibitor_class(inhibitor_module_path: str) -> Type[Inhibitor]:
        try:
            module_name = "__wakepy_inhibitor"
            spec = importlib.util.spec_from_file_location(
                module_name, inhibitor_module_path
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except ImportError as e:
            raise ImportError(
                f"{e} | Used python interpreter: {sys.executable}."
            ) from e
        return module.Inhibitor

    def uninhibit(self) -> None:
        """Uninhibit what was inhibited. In case the operation fails, raises a
        RuntimeError."""
        if self._inhibitor:
            self._inhibitor.stop()
            self._inhibitor = None
        else:
            warnings.warn("Called uninhibit before inhibit -> doing nothing.")

    def send_message(self, client_socket: socket, message: str) -> None:
        client_socket.sendall(message.encode())

    def check_for_quit_message(self, sock: socket) -> bool:
        # waits until the socket gets a message
        try:
            request = sock.recv(1024).decode()
        except TimeoutError:
            return False
        print(f"Received request: {request}")
        # if the client disconnects, empty string is returned. This will make
        # sure that the server process quits automatically when it's not needed
        # anymore.
        return request == "QUIT" or request == ""


if __name__ == "__main__":
    # This is the entry point for the inhibitor server, and it's called
    # automatically when using the start_inhibit_server()

    if len(sys.argv) < 3:
        print(
            f"Usage: python {__file__} <socket_path> <inhibitor_module> "
            "[inhibit_args...]"
        )
        sys.exit(1)

    # Get the socket path from the command-line arguments
    InhibitorServer().run(
        socket_path=sys.argv[1], inhibitor_module=sys.argv[2], *sys.argv[3:]
    )
