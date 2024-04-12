from __future__ import annotations

import sys
import typing
from pathlib import Path
from typing import Any

from tox.config.cli.parse import get_options
from tox.plugin import impl

if typing.TYPE_CHECKING:
    from tox.config.cli.parser import ToxParser
    from tox.tox_env.api import ToxEnv


dist_dir = Path(__file__).resolve().parent / "dist"
tox_asks_rebuild = dist_dir / ".TOX-ASKS-REBUILD"


@impl
def tox_on_install(tox_env: ToxEnv, arguments: Any, section: str, of_type: str) -> None:
    """Make it possible to have tox packaging environment for setting
    "package=external" (.pkg_external) which builds the wheel *only once*, or
    zero times if --skip-build command line argument is given.

    Explanation
    -----------
    The tox_on_install is one of the available tox hooks[1]. What we are
    here after is the tox_on_intall hook call of the ".pkg_external"
    environment, which is called max once per tox invocation, before any
    commands of other environments are executed. This makes it possible to
    build wheel just once and use it in multiple tox environments. See tox
    #2729[2].

    [1]: https://tox.wiki/en/4.14.2/plugins.html
    [2]: https://github.com/tox-dev/tox/issues/2729
    """

    print(f"Called tox_on_intall hook ({tox_env.name}, {of_type})")

    # (1) The tox_env of .pkg_external is passed here only if the package needs
    # to be built; only if tox is run with at least one environment with
    # skip_install not set to True. This requires the "package = external"
    # setting in the [testenv] of tox.ini.
    # (2) There are two matches for `of_type`: 'requires' and 'deps'. We want
    # to only match once. (but it does not matter which one of them)
    if (tox_env.name != ".pkg_external") or (of_type != "requires"):
        return

    options = get_options(*sys.argv[1:])
    if options.parsed.skip_build:
        print("Skipping build (--skip-build selected)")
        return

    print(f"Creating {tox_asks_rebuild}")
    # Create a dummy file which tells to the build script that the package
    # should be built.
    tox_asks_rebuild.parent.mkdir(parents=True, exist_ok=True)
    tox_asks_rebuild.touch()


@impl
def tox_add_option(parser: ToxParser) -> None:
    """Adds custom option, --skip-build to the tox command."""
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help=(
            "Skip building the python distribution package (wheel). This essentially "
            "means that tox runs tests against the wheel found in the dist/ directory. "
            "The main purpose of this flag is to make it possible to run tests in CI "
            "pipelines against a wheel created in a previous step. "
        ),
    )
