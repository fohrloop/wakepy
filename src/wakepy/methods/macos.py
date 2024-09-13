from __future__ import annotations

import logging
import typing
from abc import ABC, abstractmethod
from subprocess import PIPE, Popen

from wakepy.core import Method, ModeName, PlatformType

if typing.TYPE_CHECKING:
    from typing import Optional


class _MacCaffeinate(Method, ABC):
    """This is a method which calls the `caffeinate` command.

    Docs: https://ss64.com/osx/caffeinate.html
    Also: https://web.archive.org/web/20140604153141/https://developer.apple.com/library/mac/documentation/Darwin/Reference/ManPages/man8/caffeinate.8.html
    """

    supported_platforms = (PlatformType.MACOS,)

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.logger = logging.getLogger(__name__)
        self._process: Optional[Popen[bytes]] = None

    def enter_mode(self) -> None:
        self.logger.debug('Running "%s"', self.command)
        self._process = Popen(self.command.split(), stdin=PIPE, stdout=PIPE)

    def exit_mode(self) -> None:
        if self._process is None:
            self.logger.debug("No need to terminate process (not started)")
            return
        self.logger.debug('Terminating process ("%s")', self.command)
        self._process.terminate()
        self._process.wait()

    @property
    @abstractmethod
    def command(self) -> str: ...


class CaffeinateKeepRunning(_MacCaffeinate):
    mode_name = ModeName.KEEP_RUNNING
    command = "caffeinate"
    name = "caffeinate"


class CaffeinateKeepPresenting(_MacCaffeinate):
    mode_name = ModeName.KEEP_PRESENTING
    # -d:  Create an assertion to prevent the display from sleeping.
    command = "caffeinate -d"
    name = "caffeinate"
