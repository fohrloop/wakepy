import os

# Some environment variables
WAKEPY_FAKE_SUCCESS = "WAKEPY_FAKE_SUCCESS"


def fake_success() -> bool:
    """Function which says if fake success should be enabled

    Fake success is controlled via WAKEPY_FAKE_SUCCESS environment variable.
    If that variable is set to non-empty value, fake success is activated.

    Motivation:
    -----------
    When running on CI system, wakepy might fail to acquire an inhibitor lock
    just because there is no Desktop Environment running. In these cases, it
    might be useful to just tell with an environment variable that wakepy
    should fake the successful inhibition anyway. Faking the success is done
    after every other method is tried (and failed).
    """
    if os.environ.get(WAKEPY_FAKE_SUCCESS):
        return True
    return False
