"""Common terms and definitions used in many places"""

import sys
from typing import List, Set, Tuple, TypeVar, Union

from .strenum import StrEnum, auto

if sys.version_info < (3, 8):  # pragma: no-cover-if-py-gte-38
    from typing_extensions import Literal
else:  # pragma: no-cover-if-py-lt-38
    from typing import Literal

WAKEPY_FAKE_SUCCESS = "WAKEPY_FAKE_SUCCESS"
"""Name of the Wakepy fake success method and the environment variable used
to set it"""

# This variable should only contain lower-case characters.
FALSY_ENV_VAR_VALUES = ("0", "no", "false", "n", "f", "")
"""The falsy environment variable values. All other values are considered to be
truthy. These values are case insensitive; Also "NO", "False" and "FALSE" are
falsy.
"""


class PlatformName(StrEnum):
    """All the different platforms wakepy knows about. Any platform that is not
    detected will be named ``OTHER``."""

    WINDOWS = auto()

    LINUX = auto()

    MACOS = auto()
    """Mac OS (Darwin)"""

    OTHER = auto()
    """Anything else"""


PlatformNameValue = Literal["WINDOWS", "LINUX", "MACOS", "OTHER"]


class ModeName(StrEnum):
    """The names of the modes wakepy supports

    See: wakepy/modes/keep.py for full definitions of the modes.
    """

    KEEP_RUNNING = "keep.running"
    KEEP_PRESENTING = "keep.presenting"


ModeNameValue = Literal["keep.running", "keep.presenting"]


class BusType(StrEnum):
    """Type of D-Bus bus."""

    SESSION = auto()
    SYSTEM = auto()


BusTypeValue = Literal["SESSION", "SYSTEM"]


class StageName(StrEnum):
    # These are stages which occur in order for each of the methods
    # when using a Method for activation.

    NONE = auto()  # No stage at all.

    # The stages in the activation process in order
    PLATFORM_SUPPORT = auto()
    REQUIREMENTS = auto()
    ACTIVATION = auto()


StageNameValue = Literal["NONE", "PLATFORM_SUPPORT", "REQUIREMENTS", "ACTIVATION"]

# Type annotations
T = TypeVar("T")
Collection = Union[List[T], Tuple[T, ...], Set[T]]
StrCollection = Collection[str]
