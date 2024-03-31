"""This module is used solely by tox and is meant for the .pkg_external
environment. See tox.ini for more details.
"""

import shutil
import subprocess
import sys
from pathlib import Path

dist_dir = Path(__file__).resolve().parent.parent / "dist"
tox_asks_rebuild = dist_dir / ".TOX-ASKS-REBUILD"


def build():
    print(f"Checking {tox_asks_rebuild}")
    if not tox_asks_rebuild.exists():
        print("Build already done. skipping.")
        return

    print(f"Removing {dist_dir} and building sdist and wheel into {dist_dir}")
    # Cleanup. Remove all older builds; the /dist folder and its contents.
    # Note that tox would crash if there were two files with .whl extension.
    # This also resets the TOX-ASKS-REBUILD so we build only once.
    shutil.rmtree(dist_dir, ignore_errors=True)

    # This creates first sdist from the source tree and then wheel from the
    # sdist. By running tests agains the wheel we test all, the source tree,
    # the sdist and the wheel.

    out = subprocess.run(
        f"python -m build --no-isolation -o {dist_dir}",
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=True,
    )

    if out.returncode != 0:
        print("\n", end="")
        raise subprocess.CalledProcessError(out.returncode, out.args)


if __name__ == "__main__":

    build()
