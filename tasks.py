"""Defines following commands which use Invoke[1].

invoke format
* Format the files automatically

invoke check
* Check the formatting, type hints, etc.

invoke docs
* Start sphinx build for documentation

invoke test
* Runs tests and coverage (does not test build)

In addition to these, tox is an important command. Running `tox` will
run tests with multiple versions of python (if available on the system), run
checks (same as in invoke check) and test building the docs.

[1] https://docs.pyinvoke.org/
"""

from invoke import task
import platform
from colorama import Fore


def get_run_with_print(c):
    def run_with_print(cmd: str):
        print("Running:", Fore.YELLOW, cmd, Fore.RESET)
        c.run(cmd, pty=platform.system() == "Linux")

    return run_with_print


@task
def format(c):
    run = get_run_with_print(c)
    run("python -m isort ./wakepy")
    run("python -m black ./wakepy")
    run("python -m ruff check --fix ./wakepy")


@task
def check(c):
    run = get_run_with_print(c)
    run("python -m isort --check ./wakepy")
    run("python -m black --check ./wakepy")
    run("python -m ruff check --no-fix ./wakepy")
    run("python -m mypy ./wakepy")


@task
def docs(c):
    """Starts sphinx build with live-reload on browser."""

    run = get_run_with_print(c)
    # The `-a` flag ensures that *all* files (not only edited files) will get
    # rebuild. You may also build just once with
    #   sphinx-build -b html docs/source/ docs/build
    run("sphinx-autobuild docs/source/ docs/build/ -a")


@task
def test(c, pdb: bool = False):
    run = get_run_with_print(c)
    pdb_flag = " --pdb " if pdb else ""
    run(
        f"python -m pytest {pdb_flag}--cov-branch --cov wakepy && coverage html && "
        "python -m webbrowser -t htmlcov/index.html"
    )
