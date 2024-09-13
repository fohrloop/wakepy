from __future__ import annotations

import platform
import typing
import warnings

from .constants import IdentifiedPlatformType, PlatformType

if typing.TYPE_CHECKING:
    from typing import Callable, Tuple

    PlatformFunc = Callable[[IdentifiedPlatformType], bool]


def get_current_platform() -> IdentifiedPlatformType:
    # Ref: https://docs.python.org/3/library/platform.html#platform.system
    system = platform.system()
    if system == "Windows":
        return IdentifiedPlatformType.WINDOWS
    elif system == "Darwin":
        return IdentifiedPlatformType.MACOS
    elif system == "Linux":
        return IdentifiedPlatformType.LINUX
    elif system == "FreeBSD":
        return IdentifiedPlatformType.FREEBSD

    # LATER: This should be improved in https://github.com/fohrloop/wakepy/issues/378
    warnings.warn(
        f"Could not detect current platform! platform.system() returned {system}"
    )
    return IdentifiedPlatformType.UNKNOWN


CURRENT_PLATFORM: IdentifiedPlatformType = get_current_platform()
"""The current platform as detected. If the platform cannot be detected,
defaults to ``UNKNOWN``."""


def get_platform_supported(
    platform: IdentifiedPlatformType, supported_platforms: Tuple[PlatformType, ...]
) -> bool | None:
    """Checks if a platform is in the supported platforms.

    Parameters
    ----------
    platform: IdentifiedPlatformType
        The platform to check.
    supported_platforms:
        The platforms to check against.

    Returns
    -------
    is_supported: bool | None
        If platform is supported, returns True. If the support is unknown,
        returns None, and if the platform is not supported, returns False.
    """
    for supported_platform in supported_platforms:
        func = PLATFORM_INFO_FUNCS[supported_platform]
        if func(platform) is True:
            return True
    if is_unknown(platform):
        return None
    return False


def is_windows(current_platform: IdentifiedPlatformType) -> bool:
    return current_platform == IdentifiedPlatformType.WINDOWS


def is_linux(current_platform: IdentifiedPlatformType) -> bool:
    return current_platform == IdentifiedPlatformType.LINUX


def is_freebsd(current_platform: IdentifiedPlatformType) -> bool:
    return current_platform == IdentifiedPlatformType.FREEBSD


def is_macos(current_platform: IdentifiedPlatformType) -> bool:
    return current_platform == IdentifiedPlatformType.MACOS


def is_bsd(current_platform: IdentifiedPlatformType) -> bool:
    return is_freebsd(current_platform)


def is_unknown(current_platform: IdentifiedPlatformType) -> bool:
    return current_platform == IdentifiedPlatformType.UNKNOWN


def is_unix_like_foss(current_platform: IdentifiedPlatformType) -> bool:
    return is_bsd(current_platform) or is_linux(current_platform)


PLATFORM_INFO_FUNCS: dict[PlatformType, PlatformFunc] = {
    PlatformType.WINDOWS: is_windows,
    PlatformType.LINUX: is_linux,
    PlatformType.MACOS: is_macos,
    PlatformType.FREEBSD: is_freebsd,
    PlatformType.UNKNOWN: is_unknown,
    PlatformType.BSD: is_bsd,
    PlatformType.ANY: lambda _: True,
    PlatformType.UNIX_LIKE_FOSS: is_unix_like_foss,
}
