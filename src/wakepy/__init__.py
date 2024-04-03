# NOTE The methods sub-package is imported for registering all the methods.
from . import methods as methods

try:
    from ._version import __version__ as __version__  # type:ignore
    from ._version import version_tuple as version_tuple  # type:ignore
except ImportError:  # pragma: no cover
    # Likely an editable install. Should ever happen if installed from a
    # distribution package (sdist or wheel)
    __version__ = "undefined"
    version_tuple = (0, 0, 0, "undefined")


from .core import ActivationError as ActivationError
from .core import ActivationResult as ActivationResult
from .core import DBusAdapter as DBusAdapter
from .core import Method as Method
from .core import Mode as Mode
from .core import ModeExit as ModeExit
from .modes import keep as keep
