from __future__ import annotations

import typing
from pathlib import Path
from typing import Any

from tox.plugin import impl

if typing.TYPE_CHECKING:
    from tox.tox_env.api import ToxEnv


dist_dir = Path(__file__).resolve().parent / "dist"
tox_asks_rebuild = dist_dir / ".TOX-ASKS-REBUILD"


@impl
def tox_on_install(tox_env: ToxEnv, arguments: Any, section: str, of_type: str):
    """The tox_on_install is once of the available tox hooks[1]. What we are
    here after is the tox_on_intall hook call of the ".pkg_external"
    environment, which is called max once per tox invocation, before any
    commands of other environments are executed. The reason why this is used
    is to make it possible to build wheel just once and use it in multiple tox
    environments. See tox #2729[2]

    [1]: https://tox.wiki/en/4.14.2/plugins.html
    [2]: https://github.com/tox-dev/tox/issues/2729
    """

    # (1) The tox_env of .pkg_external is passed here only if the package needs
    # to be built; only if tox is run with at least one environment with
    # skip_install not set to True. This requires the "package = external"
    # setting in the [testenv] of tox.ini.
    # (2) There are two matches for `of_type`: 'requires' and 'deps'. We want
    # to only match once. (but it does not matter which one of them)
    print(f"Called tox_on_intall hook ({tox_env.name}, {of_type})")
    if (tox_env.name != ".pkg_external") or (of_type != "requires"):
        return

    print(f"Creating {tox_asks_rebuild}")
    # Create a dummy file which tells to the build script that the package
    # should be built.
    tox_asks_rebuild.parent.mkdir(parents=True, exist_ok=True)
    tox_asks_rebuild.touch()
