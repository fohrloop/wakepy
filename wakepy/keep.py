import contextlib
from typing import Iterator

from ._deprecated import get_function


class ModeInfoTemporaryImplementation:
    """This is the class returned by the wakepy mode switching context
    managers. The API is just under development, and therefore the name of this
    class will change.

    What is not going to be changed:
    * self.success
    * self.failure

    The abovementioned parts can be assumed to be present in the returned
    object also in the future.
    """

    def __init__(self):
        self.success: bool = False
        """Tells is entering into a mode was succesful. Note that this
        may be faked with WAKEPY_FAKE_SUCCESS environment variable.
        """

        self.real_success: bool = False
        """Tells is entering into a mode was succesful. This 
        may not faked with WAKEPY_FAKE_SUCCESS environment variable.
        """

    @property
    def failure(self) -> bool:
        """The opposite of self.success. If this is True, entering into
        the mode has failed. This may be faked with WAKEPY_FAKE_SUCCESS
        environment variable."""
        return not self.success


def _temporary_solution_for_using_old_functions_with_new_api(
    keep_screen_awake=False,
) -> Iterator[ModeInfoTemporaryImplementation]:
    # This is a toy implementation using the old, deprecated functions
    # They're only used in wakepy 0.6.x, and new, better implementation
    # will be replacing this in wakepy 0.7.0
    set_keepawake = get_function("set_keepawake")
    unset_keepawake = get_function("unset_keepawake")

    m = ModeInfoTemporaryImplementation()
    try:
        result = set_keepawake(keep_screen_awake=keep_screen_awake)
    except Exception:
        m.success = False
    else:
        m.success = True
        if result in (True, False):
            m.real_success = result
        else:
            raise ValueError("Expected True or False")

    try:
        yield m
    finally:
        unset_keepawake()


@contextlib.contextmanager
def running():
    """Keep the system running your programs; Prevent system from sleeping /
    suspending automatically. Does not keep display on, and does not prevent
    automatic screen lock or screen saver.

    Example
    -------
    .. code-block::

        from wakepy import keep

        with keep.running() as m:
            if not m.success:
                # optional: signal to user?

            # Do something that takes a long time but does not need to be
            # displayed.

    """

    yield from _temporary_solution_for_using_old_functions_with_new_api(
        keep_screen_awake=False
    )


@contextlib.contextmanager
def presenting():
    """Keep the system running your programs and showing some content; Prevent
    screen saver and screen locker from switching on. Implies that system is
    prevented from  sleeping / suspending automatically.

    Example
    -------
    .. code-block::

        from wakepy import keep

        with keep.presenting() as m:
            if not m.success:
                # optional: signal to user?

            # Do something that takes a long time and needs
            # to be shown to user; no automatic screen lock


    .. warning::

        🔒 Since screen will not be automatically locked, you don't want to leave
        your machine unattended in an insecure place.

    """

    yield from _temporary_solution_for_using_old_functions_with_new_api(
        keep_screen_awake=True
    )
