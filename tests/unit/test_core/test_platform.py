import re
import textwrap
from unittest.mock import patch

import pytest

from wakepy.core import PlatformType
from wakepy.core.constants import IdentifiedPlatformType
from wakepy.core.platform import (
    get_current_platform,
    get_platform_debug_info,
    get_platform_debug_info_dict,
    get_platform_supported,
)

P = IdentifiedPlatformType


class TestGetCurrentPlatform:

    @patch("platform.system", lambda: "Windows")
    def test_windows(self):
        assert get_current_platform() == PlatformType.WINDOWS

    @patch("platform.system", lambda: "Darwin")
    def test_macos(self):
        assert get_current_platform() == PlatformType.MACOS

    @patch("platform.system", lambda: "Linux")
    def test_linux(self):
        assert get_current_platform() == PlatformType.LINUX

    @patch("platform.system", lambda: "FreeBSD")
    def test_bsd(self):
        assert get_current_platform() == PlatformType.FREEBSD

    @patch("platform.system", lambda: "This does not exist")
    def test_other(self):
        with pytest.warns(UserWarning, match="Could not detect current platform!"):
            assert get_current_platform() == PlatformType.UNKNOWN


class TestPlatformSupported:
    """tests for get_platform_supported"""

    def test_windows(self):

        # On Windows, anything that supports Windows is supported.
        assert get_platform_supported(P.WINDOWS, (PlatformType.WINDOWS,)) is True
        assert (
            get_platform_supported(
                P.WINDOWS,
                (PlatformType.MACOS, PlatformType.WINDOWS, PlatformType.LINUX),
            )
            is True
        )

        # If there is no windows in the supported platforms, get False
        assert get_platform_supported(P.WINDOWS, (PlatformType.LINUX,)) is False
        assert (
            get_platform_supported(P.WINDOWS, (PlatformType.LINUX, PlatformType.BSD))
            is False
        )
        # Unless there is ANY, which means anything is supported
        assert (
            get_platform_supported(
                P.WINDOWS, (PlatformType.LINUX, PlatformType.BSD, PlatformType.ANY)
            )
            is True
        )

    def test_unknown(self):
        # Unknown platform is always "unknown"; returns None
        assert get_platform_supported(P.UNKNOWN, (PlatformType.WINDOWS,)) is None
        assert get_platform_supported(P.UNKNOWN, (PlatformType.LINUX,)) is None
        # .. unless "ANY" is supported.
        assert get_platform_supported(P.UNKNOWN, (PlatformType.ANY,)) is True

    def test_freebsd(self):

        assert get_platform_supported(P.FREEBSD, (PlatformType.WINDOWS,)) is False
        assert get_platform_supported(P.FREEBSD, (PlatformType.FREEBSD,)) is True
        # FreeBSD is BSD
        assert get_platform_supported(P.FREEBSD, (PlatformType.BSD,)) is True
        # FreeBSD is unix like
        assert get_platform_supported(P.FREEBSD, (PlatformType.UNIX_LIKE_FOSS,)) is True

    def test_linux(self):

        assert get_platform_supported(P.LINUX, (PlatformType.WINDOWS,)) is False
        assert get_platform_supported(P.LINUX, (PlatformType.LINUX,)) is True
        # Linux is unix like
        assert get_platform_supported(P.LINUX, (PlatformType.UNIX_LIKE_FOSS,)) is True


def test_get_platform_debug_info_dict():
    info_dct = get_platform_debug_info_dict()
    assert isinstance(info_dct, dict)

    for key, val in info_dct.items():
        assert isinstance(key, str)
        assert isinstance(val, str)


def test_get_platform_debug_info():
    debug_info = get_platform_debug_info()
    expected_out = textwrap.dedent(
        r"""
    - os.name: .*
    - sys.platform: .*
    - platform.system\(\): .*
    - platform.release\(\): .*
    - platform.machine\(\): .*
    - sysconfig.get_platform\(\): .*
    .*
    """.strip(
            "\n"
        )
    )
    assert re.match(expected_out, debug_info)
