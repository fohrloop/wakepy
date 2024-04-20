"""This module defines the WakepyFakeSuccess method, which can be used to fake
activation success. It is controlled with the WAKEPY_FAKE_SUCCESS environment
variable"""

from wakepy.core import CURRENT_PLATFORM, Method
from wakepy.core.constants import WAKEPY_FAKE_SUCCESS


class WakepyFakeSuccess(Method):
    """This is a special fake method to be used with any mode. It can be used
    in tests for faking wakepy mode activation. This way all IO and real
    executable, library and dbus calls are prevented. To use this method (and
    skip using any other methods), set WAKEPY_FAKE_SUCCESS environment variable
    to a truthy value (e.g. "1", or "True").
    """

    name = WAKEPY_FAKE_SUCCESS
    mode = "_fake"

    environment_variable = name

    # All other values are considered to be truthy. Comparison is case
    # insensitive
    falsy_values = ("0", "no", "false")

    supported_platforms = (CURRENT_PLATFORM,)

    def enter_mode(self) -> None:
        """Function which says if fake success should be enabled

        Fake success is controlled via WAKEPY_FAKE_SUCCESS environment
        variable. If that variable is set to a truthy value,fake success is
        activated.

        Falsy values: '0', 'no', 'false' (case ignored)
        Truthy values: everything else

        Motivation:
        -----------
        When running on CI system, wakepy might fail to acquire an inhibitor
        lock just because there is no Desktop Environment running. In these
        cases, it might be useful to just tell with an environment variable
        that wakepy should fake the successful inhibition anyway. Faking the
        success is done after every other method is tried (and failed).
        """
        # The os.environ seems to be populated when os is imported -> delay the
        # import until here.
        import os

        if self.environment_variable not in os.environ:
            raise RuntimeError(f"{self.environment_variable} not set.")

        val = os.environ[self.environment_variable]
        if val.lower() in self.falsy_values:
            raise RuntimeError(
                f"{self.environment_variable} set to falsy value: {val}."
            )
