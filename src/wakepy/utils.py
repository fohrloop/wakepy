from __future__ import annotations

import subprocess
import time
import typing
from pathlib import Path

if typing.TYPE_CHECKING:
    from typing import Iterable

search_directories = [
    "/usr/bin",  # default python used by a unix system
    "/usr/local/bin",  # python installed by the user is typically here
]


def get_python_path(required_modules: list[str] | None) -> str | None:
    """Gets the path to the system python interpreter which has the required
    modules."""
    for python in iter_python3_executable_paths(search_directories):
        if required_modules:
            if not has_modules(python, required_modules):
                continue
        return python


def iter_python3_executable_paths(directories: Iterable[str]):
    for directory in directories:
        executable = Path(directory) / "python3"
        if not executable.exists():
            continue
        yield executable


def has_modules(python: str, modules: list[str]) -> bool:
    """Checks if the python interpreter has the required modules."""
    t1 = time.time()
    cmd = (
        "from importlib.util import find_spec;"
        f"""print(all(find_spec(module) for module in {modules}),end='')"""
    )
    out = subprocess.run([python, "-c", cmd], check=True, capture_output=True)
    t2 = time.time()
    print("took", t2 - t1)
    return out.stdout == b"True"


if __name__ == "__main__":
    import time

    t1 = time.time()
    print(get_python_path(["gi"]))
    t2 = time.time()
    print(t2 - t1)
