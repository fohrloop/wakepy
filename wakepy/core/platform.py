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
        with open("/proc/version", "r") as f:
            kernel_version_str = f.readline().lower()
    
        # This should support both versions of WSL.
        is_wsl = "microsoft" in kernel_version_str or "wsl" in kernel_version_str
        return PlatformName.LINUX if not is_wsl else PlatformName.WSL

    warnings.warn(
        f"Could not detect current platform! platform.system() returned {system}"
    )
    return PlatformName.OTHER


CURRENT_PLATFORM = get_current_platform()
