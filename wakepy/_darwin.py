from subprocess import Popen, PIPE

COMMAND = u'caffeinate'
ARGS = u" -d"
BREAK = '\003'

_process = None


def set_keepawake(keep_screen_awake=False):
    """
    Set the keep-awake. During keep-awake, the CPU is not allowed to go to sleep
    automatically until the `unset_keepawake` is called.

    Parameters
    -----------
    keep_screen_awake: bool
        If True, keeps also the screen awake.
    """
    if keep_screen_awake:
        global _process
        _process = Popen([COMMAND], stdin=PIPE, stdout=PIPE)
    else:
        _process = Popen(COMMAND + ARGS, stdin=PIPE, stdout=PIPE)


def unset_keepawake():
    global _process
    _process.stdin.write(BREAK)
    _process.stdin.flush()
    _process.stdin.close()
    _process.wait()
