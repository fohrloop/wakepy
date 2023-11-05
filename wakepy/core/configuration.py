import platform

from .definitions import SystemName

# E.g.: 'windows', 'linux' or 'darwin'
# TODO: consider splitting this information to "platform", which would also include wsl
# and cygwin and "os" which would just tell the operating system?
CURRENT_SYSTEM = SystemName(platform.system().lower())
