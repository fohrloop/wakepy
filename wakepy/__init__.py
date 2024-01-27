# NOTE The methods sub-package is imported for registering all the methods.
from . import methods as methods
from .core import ActivationError as ActivationError
from .core import ActivationResult as ActivationResult
from .core import DbusAdapter as DbusAdapter
from .core import Method as Method
from .core import Mode as Mode
from .core import ModeExit as ModeExit
from .modes import keep as keep

__version__ = "0.8.0dev"
