from __future__ import annotations

import logging
import subprocess
import sys
import time
import uuid
from importlib import import_module
from pathlib import Path
from socket import AF_UNIX, SOCK_STREAM, socket

if sys.version_info < (3, 8):  # pragma: no-cover-if-py-gte-38
    from typing_extensions import Protocol
else:  # pragma: no-cover-if-py-lt-38
    from typing import Protocol

logger = logging.getLogger(__name__)

# Path to the Unix domain socket file
SOCKET_PATH_TEMPLATE = "/tmp/wakepy/wakepy-pyinhibit-subprocess-{id}.socket"

SYSTEM_PYTHON_PATH = "/usr/bin/python3"

inhibitor_server_path = Path(__file__).parent / "inhibitor_server.py"


class Inhibitor(Protocol):
    """The Inhibitor protocol. An inhibitor module should provide a class
    called Inhibitor which implements this protocol."""

    def start(self, *args) -> None: ...
    def stop(self) -> None: ...


def get_inhibitor(inhibitor_module: str) -> Inhibitor:
    """Import the inhibitor module from path specified by `inhibitor_module`
    and return the Inhibitor class. If the module is not found in the current
    python environment, a SubprocessInhibor using system python is returned,
    instead."""

    try:
        module = import_module(inhibitor_module)
        inhibitor = module.Inhibitor()
        logger.debug(
            "Inhibitor module '%s' loaded to local python environment", inhibitor_module
        )
        return inhibitor
    except ImportError:

        inhibitor = SubprocessInhibor(
            socket_path=get_socket_path(),
            python_path=SYSTEM_PYTHON_PATH,
            inhibitor_path=get_module_path(inhibitor_module),
        )
        logger.debug(
            'Inhibitor module "%s" not found in the current python environment. '
            'Trying to use "%s" instead.',
            inhibitor_module,
            SYSTEM_PYTHON_PATH,
        )
        return inhibitor


def get_socket_path() -> str:
    socket_path = SOCKET_PATH_TEMPLATE.format(id=uuid.uuid4())
    Path(socket_path).parent.mkdir(parents=True, exist_ok=True)
    return socket_path


def get_module_path(inhibitor_module: str) -> Path:
    """Get the path to the module specified by `inhibitor_module`.

    Parameters
    ----------
    inhibitor_module : str
        The module path, like "wakepy.methods.gtk.inhibitor". Note that this
        function only supports modules (not packages), and that the file
        extension of the modules is assumed to be ".py". All module paths must
        start with "wakepy."

    Returns
    -------
    Path:
        The path to the module file. For example:
        PosixPath('/home/user/venv/wakepy/methods/gtk/inhibitor.py')

    """
    import wakepy

    if not inhibitor_module.startswith("wakepy."):
        raise ValueError("The module path must start with 'wakepy.'")

    wakepy_path = Path(wakepy.__file__).parent
    path_parts = inhibitor_module.split(".")[1:]
    return wakepy_path.joinpath(*path_parts).with_suffix(".py")


class SubprocessInhibor:
    """Runs Inhibitor in a subproces; Runs a inhibitor server with the given
    python interpreter and the inhibitor module. This is an alternative way
    of using an inhibitor module (needed when required modules are not
    available in the current python environment)."""

    def __init__(
        self,
        socket_path: str,
        python_path: str,
        inhibitor_path: str,
    ):
        self.socket_path = socket_path
        self.python_path = python_path
        self.inhibitor_path = inhibitor_path
        self.client_socket: socket | None = None

    def start(self, *args) -> None:

        start_inhibit_server(
            self.socket_path,
            self.python_path,
            self.inhibitor_path,
            *args,
        )

        self.client_socket = get_client_socket(self.socket_path)

        try:
            get_and_handle_inhibit_result(self.client_socket)
        except Exception:
            self.client_socket.close()
            raise

    def stop(self) -> None:

        try:
            send_quit(self.client_socket)
        finally:
            self.client_socket.close()

        Path(self.socket_path).unlink(missing_ok=True)


def start_inhibit_server(
    socket_path: str, python_path: str, inhibitor_path: str, *inhibitor_args: object
):
    """Starts the pyinhibitor server.

    Parameters
    ----------
    python_path : str
        The path to the python interpreter
    inhibitor_path: str
        The path to the inhibitor python module. This module must contain a
        class called Inhibitor which implements the Inhibitor protocol.
    """
    socket_pth = Path(socket_path).expanduser()
    # Remove the file so we can just wait the file to appear and know that
    # the server is ready.
    socket_pth.unlink(missing_ok=True)

    cmd = [
        python_path,
        str(inhibitor_server_path),
        socket_path,
        inhibitor_path,
        *inhibitor_args,
    ]
    subprocess.Popen(cmd)
    try:
        wait_until_file_exists(socket_pth)
    except Exception as e:
        raise RuntimeError(f"Something went wrong while calling {cmd}") from e


def wait_until_file_exists(
    file_path: Path, total_wait_time: float = 2, wait_time_per_cycle=0.001
) -> None:
    """Waits until a file exists or the total_wait_time is reached.

    Parameters
    ----------
    file_path : Path
        The path to the file
    total_wait_time : float, optional
        The total time to wait. Default: 2 (seconds)
    wait_time_per_cycle : float, optional
        The time to wait between each cycle. Default: 0.001 (seconds)

    Raises
    ------
    FileNotFoundError
        If the file does not exist after the total_wait_time
    """

    for _ in range(int(total_wait_time / wait_time_per_cycle)):
        if file_path.exists():
            break
        time.sleep(wait_time_per_cycle)
    else:
        raise FileNotFoundError(f"File {file_path} does not exists. Wait")


def get_client_socket(socket_path: str) -> socket:
    client_socket = socket(AF_UNIX, SOCK_STREAM)
    try:
        client_socket.connect(socket_path)
    except ConnectionRefusedError:
        raise RuntimeError("Must start the server first.")
    client_socket.settimeout(1)
    return client_socket


def get_and_handle_inhibit_result(client_socket: socket):
    response = _get_response_from_server(client_socket)

    if response.startswith("INHIBIT_ERROR"):
        errtext = response.split(":", maxsplit=1)[1]
        raise RuntimeError(errtext)
    elif response != "INHIBIT_OK":  # should never happen
        raise RuntimeError("Failed to inhibit the system")


def send_quit(client_socket: socket):
    client_socket.sendall("QUIT".encode())
    response = _get_response_from_server(client_socket)

    if response.startswith("UNINHIBIT_ERROR"):
        errtext = response.split(":", maxsplit=1)[-1]
        raise RuntimeError(f"Failed to uninhibit the system: {errtext}")
    elif response != "UNINHIBIT_OK":  # should never happen
        raise RuntimeError("Failed to uninhibit the system")


def _get_response_from_server(client_socket: socket) -> str:
    response = client_socket.recv(1024).decode()
    logger.debug("Response from pyinhibitor server: %s", response)
    return response
