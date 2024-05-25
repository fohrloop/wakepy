(wakepy-modes)=
# Wakepy Modes

Wakepy Modes are states that you activate, and while the mode is active, wakepy keeps the system awake (inhibits suspend/sleep). In the end you deactivate the mode. Each Mode is implemented with multiple [Methods](#wakepy-methods) which support different platforms. Wakepy selects the used Method automatically, but it may also be selected by the user. The available modes are

| Wakepy mode              | [keep.running](#keep-running-mode) | [keep.presenting](#keep-presenting-mode)|
| ------------------------ | ------------ | --------------- |
| Sleep is prevented       | Yes          | Yes             |
| Screenlock is prevented  | No[^win-slock]          | Yes             |
| Screensaver is prevented | No          | Yes             |

[^win-slock]: Depending on system settings, it is possible that Windows will not automatically lock the system, because Windows will lock the screen either when (1) returning from suspend (which is now inhibited) or (2) when returning from Screen Saver, *if ScreenSaverIsSecure is set or enforced by a Group Policy (GPO)*.  See: [wakepy/#169](https://github.com/fohrloop/wakepy/issues/169)

```{note}
The table above only considers the *automatic* actions (go to sleep, start screenlock, start screensaver), which are based on the *idle timer*; It is still possible to put system to sleep by selecting Suspend/Sleep from a menu, closing the laptop lid or pressing a power key, for example. It is also possible to manually lock the session/screen or start screensaver.
```


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

**How to use wakepy in tests / CI**: One problem with tests and/or CI systems is that many times the environment is different, and preventing system going to sleep works differently there. To fake a successful inhibit lock in tests, you may set an environment variable: [`WAKEPY_FAKE_SUCCESS`](#WAKEPY_FAKE_SUCCESS) to a truthy value like `1`.