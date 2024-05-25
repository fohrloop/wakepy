"""This module is used solely by tox and is meant for the .pkg_external
environment. See tox.ini for more details.
"""

import shutil
import subprocess
import sys
from pathlib import Path

dist_dir = Path(__file__).resolve().parent.parent / "dist"
tox_asks_rebuild = dist_dir / ".TOX-ASKS-REBUILD"

# A list of errors to skip.
skip_errors = [
    # This occurs every time sdist is used to create wheel as git files are not
    # included in the sdist (on every build.)
    "ERROR setuptools_scm._file_finders.git listing git files failed - pretending there aren't any"  # noqa: E501
]


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
        stderr=subprocess.PIPE,
        shell=True,
        universal_newlines=True,
    )

    errors = [err for err in out.stderr.split("\n") if err and err not in skip_errors]
    if errors:
        sys.stderr.write("Captured errors:\n")
        for line in errors:
            sys.stderr.write(line)

    if out.returncode != 0:
        print("\n", end="")
        raise subprocess.CalledProcessError(out.returncode, out.args)


if __name__ == "__main__":

    build()
