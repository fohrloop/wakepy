import platform

from .constants import PlatformName

# E.g.: 'windows', 'linux' or 'darwin'
# TODO: consider splitting this information to "platform", which would also include wsl
# and cygwin and "os" which would just tell the operating system?
CURRENT_PLATFORM = PlatformName(platform.system().lower())
