"""Defines following commands which use Invoke[1].

invoke format
* Format the files automatically

invoke check
* Check the formatting, type hints, etc.

invoke docs
* Start sphinx build for documentation

invoke test
* Runs tests and coverage (does not test docs build)

In addition to these, tox is an important command. Running `tox` will
run tests with multiple versions of python (if available on the system), run
checks (same as in invoke check) and test building the docs.

[1] https://docs.pyinvoke.org/
"""

from __future__ import annotations

import platform
import typing

from colorama import Fore
from invoke import task  # type: ignore

if typing.TYPE_CHECKING:
    from invoke.runners import Result


def get_run_with_print(c):
    def run_with_print(cmd: str, ignore_errors: bool = False) -> Result:
        print("Running:", Fore.YELLOW, cmd, Fore.RESET)
        res: Result = c.run(cmd, pty=platform.system() == "Linux", warn=ignore_errors)
        return res

    return run_with_print


@task
def format(c) -> None:
    run = get_run_with_print(c)
    run("python -m isort .")
    run("python -m black .")
    run("python -m ruff check --fix .")


@task
def check(c) -> None:
    run = get_run_with_print(c)
    run("python -m isort --check .")
    run("python -m black --check .")
    run("python -m ruff check --no-fix .")
    run("python -m .")


@task
def docs(c) -> None:
    """Starts sphinx build with live-reload on browser."""

    run = get_run_with_print(c)
    # The `-a` flag ensures that *all* files (not only edited files) will get
    # rebuild. You may also build just once with
    #   sphinx-build -b html docs/source/ docs/build
    run("sphinx-autobuild docs/source/ docs/build/ -a")


@task
def test(c, pdb: bool = False) -> None:
    run = get_run_with_print(c)
    pdb_flag = " --pdb " if pdb else ""
    res = run(
        f"python -m pytest {pdb_flag}--cov-branch --cov wakepy --cov-fail-under=100",
        ignore_errors=True,
    )
    if res.exited:
        run("coverage html && python -m webbrowser -t htmlcov/index.html")

    check(c)
