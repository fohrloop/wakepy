import platform
import warnings

from .constants import PlatformName


def get_current_platform() -> PlatformName:
    # Ref: https://docs.python.org/3/library/platform.html#platform.system
    system = platform.system()
    if system == "Windows":
        return PlatformName.WINDOWS
    elif system == "Darwin":
        return PlatformName.MACOS
    elif system == "Linux":
        return PlatformName.LINUX

    warnings.warn(
        f"Could not detect current platform! platform.system() returned {system}"
    )
    return PlatformName.OTHER


CURRENT_PLATFORM = get_current_platform()
