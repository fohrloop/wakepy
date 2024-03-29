# Wakepy Modes



The available modes are
| Wakepy mode                              | What it does                                        |
| ---------------------------------------- | --------------------------------------------------- |
| [keep.running](#keep-running-mode)       | Automatic sleep is prevented                        |
| [keep.presenting](#keep-presenting-mode) | Automatic sleep, screensaver & screenlock prevented |

## Entering a mode

The wakepy modes are implemented as context managers of type `wakepy.Mode`. When entering the context, the `wakepy.Mode` instance (`m`) is returned, which has following attributes:

- `m.active`: True, if entering mode was successful. Can be [faked in CI](./tests-and-ci.md#wakepy_fake_success).
- `m.activation_result`: An ActivationResult instance which gives more detailed information about the activation process.

````{tip}
You may want to inform user about failure in activating a mode. For example:

```{code-block} python
with keep.running() as m:
    if not m.active:
        print('Failed to inhibit system sleep.')

    do_something_that_takes_long_time()
```
````


(keep-running-mode)=
## keep.running

While `keep.running` mode is activated, the system may not automatically go to sleep (or
suspend) meaning that programs will continue running and can use CPU.


| Platform | DE    | Method                                                             |
| -------- | ----- | ------------------------------------------------------------------ |
| Linux    | GNOME | [org.gnome.SessionManager](#keep-running-org-gnome-sessionmanager) |
| MacOS    | *     | [caffeinate](#keep-running-macos-caffeinate)                       |
| Windows  | *     | [SetThreadExecutionState](#keep-running-windows-stes)              |


Does keep.running prevent manually putting system to sleep?
: Only the  automatical, idle timer timeout based sleep / suspend is prevented; Will not
prevent user manually entering sleep from a menu, by closing a laptop lid or by pressing
a power button, for example.

Can I lock my computer after entered `keep.running` mode?
: Yes, and you probably should, if you're not near your computer. The program will
continue execution regardless of the lock.

What about automatical lockscreen / screensaver?
: The system may still automatically log out user, enable lockscreen or turn off the
display. Automatic lock screen is not guaranteed, but it is  not prevented in any way.

What happens id the process holding the lock dies?
: The lock is automatically removed. There are no methods in keep.running mode which for
example would perform system-wide configuration changes or anything which would need
manual reversal.



(keep-presenting-mode)=
## keep.presenting

While `keep.presenting` mode is activated, the system may not automatically go to sleep (or
suspend) meaning that programs will continue running and can use CPU. In addition to
that, automatic start of screensaver & screenlock are prevented, meaning that you can
show content in the `keep.presenting` mode.


| Platform | DE              | Method                                                                      |
| -------- | --------------- | --------------------------------------------------------------------------- |
| Linux    | GNOME           | [org.gnome.SessionManager](#keep-presenting-org-gnome-sessionmanager)       |
| Linux    | GNOME + others? | [org.freedesktop.ScreenSaver](#keep-presenting-org-freedesktop-screensaver) |
| MacOS    | *               | [caffeinate](#keep-presenting-macos-caffeinate)                             |
| Windows  | *               | [SetThreadExecutionState](#keep-presenting-windows-stes)                    |

Does keep.presenting prevent manually putting system to sleep?
: Only the  automatical, idle timer timeout based sleep / suspend is prevented; Will not
prevent user manually entering sleep from a menu, by closing a laptop lid or by pressing
a power button, for example.

Can I still manually start lockscreen / screensaver?
: Yes. Only the idle timer based screensaver / lockscreen is prevented. Note that
manually entering screensaver does not deactivate the mode.


What happens id the process holding the lock dies?
: The lock is automatically removed. There are no methods in keep.presenting mode which for
example would perform system-wide configuration changes or anything which would need
manual reversal.


## General questions
**What if the process holding the lock dies?**: The lock is automatically removed.

**How to use wakepy in tests / CI**: One problem with tests and/or CI systems is that many times the environment is different, and preventing system going to sleep works differently there. To fake a successful inhibit lock in tests, you may set an environment variable: `WAKEPY_FAKE_SUCCESS` to `yes`.