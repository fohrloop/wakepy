"""Defines following commands which use Invoke[1].

invoke format
* Format the files automatically

invoke check
* Check the formatting, type hints, etc.

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
    """Starts sphinx build with live-reload on browser"""
    run = get_run_with_print(c)
    run("sphinx-autobuild docs/source/ docs/build/ -a")
