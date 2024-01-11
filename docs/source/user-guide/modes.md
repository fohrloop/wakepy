# About wakepy modes



The available modes are 
| Wakepy mode       | What it does                                        |
| ----------------- | --------------------------------------------------- |
| `keep.running`    | Automatic sleep is prevented                        |
| `keep.presenting` | Automatic sleep, screensaver & screenlock prevented |

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

## wakepy.keep.running


**Does keep.running prevent manually putting system to sleep?** All the methods, if not otherwise specified, only prevent the *automatic, idle timer timeout based* sleeping, so it is still possible to put system to sleep by selecting Suspend/Sleep from a menu, closing the laptop lid or pressing a power key, for example. One exception is systemd mask method on Linux, which prevents suspend altogether.

**Can I lock my computer after entered `keep.running` mode?**: Yes, and you probably should, if you're not near your computer. The programs will continue execution regardless of the lock.



::::{tab-set}

:::{tab-item} Windows
:sync: windows

**How it works?**:  The [SetThreadExecutionState](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate?redirectedfrom=MSDN) is called with the `ES_CONTINUOUS` and  `ES_SYSTEM_REQUIRED` flags to acquire a lock when entering the context. On exit, these flags are removed.

**How to check it?**:   Run `powercfg -requests` in an elevated PowerShell.

**Multiprocess safe?**: Yes.

:::

:::{tab-item} Linux
:sync: linux 

On wakepy 0.7.0, the current implementation of `keep.presenting` is same as of  `keep.running`. This is to be changed in a future release.


```{warning}
Current D-Bus -based implementation (v.0.7.0) incorrectly prevents also screenlock/screensaver (remember to lock manually!). This will be fixed in a future release.
```


:::

:::{tab-item} Mac
:sync: mac

**How it works?**: Wakepy launches a [`caffeinate`](https://ss64.com/osx/caffeinate.html) subprocess when setting keepawake, and terminates the subprocess when unsetting.

**How to check it?**:  There should be a subprocess visible when a lock is taken, but this is untested.

**Multiprocess safe?**: Not tested.


::: 

::::




## wakepy.keep.presenting


**Does keep.presenting prevent manually putting system to sleep?** All the methods, if not otherwise specified, only prevent the *automatic, idle timer timeout based*  sleeping and screensaver/screenlock, so it is still possible to put system to sleep by selecting Suspend/Sleep from a menu, closing the laptop lid or pressing a power key, for example. It is also possible to manually start the screenlock/screensaver while presenting mode is on. 

**Is my computer locked automatically in `keep.presenting` mode?**: No. Entering a screenlock automatically would stop presenting the content. 


::::{tab-set}

:::{tab-item} Windows
:sync: windows

**How it works?**:   The [SetThreadExecutionState](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate?redirectedfrom=MSDN) is called with the `ES_CONTINUOUS`, `ES_SYSTEM_REQUIRED` and `ES_DISPLAY_REQUIRED` flags to acquire a lock when entering the context. On exit, these flags are removed.

**How to check it?**:   Run `powercfg -requests` in an elevated PowerShell.

**Multiprocess safe?**: Yes.

::: 

:::{tab-item} Linux
:sync: linux 



**How it works?**: Wakepy uses, depending on what is installed, either (in this order)
1. D-Bus to call `Inhibit` method of [`org.freedesktop.ScreenSaver`](https://people.freedesktop.org/~hadess/idle-inhibition-spec/re01.html) (try first using jeepney, and then using dbus-python)
3. `systemctl mask`


```{warning}
The systemd mask method will inhibit all forms of sleep (including hibernation and sleep initialized by the user). It will change global system settings, so if your process exits abruptly, you'll have to undo the change.
```

**How to check it?**:  For D-Bus  `org.freedesktop.ScreenSaver` based solution, there is no possibility to check it afterwards. You may monitor the call with [`dbus-monitor`](https://dbus.freedesktop.org/doc/dbus-monitor.1.html), though. For systemd mask based solution, you'll see that the Suspend option is removed from the menu altogether.

**Which Desktop Environments are supported?** For D-Bus `org.freedesktop.ScreenSaver` method, you have to use a Freedesktop-compliant Desktop Environment, for example GNOME or KDE. The list of supported DEs will be expanded in the future. For systemd solution, any Linux running systemd works, but you need sudo.

**Multiprocess safe?**: DBus: yes, systemd mask: no.


:::



:::{tab-item} Mac
:sync: mac 

**How it works?**: Wakepy launches a [`caffeinate`](https://ss64.com/osx/caffeinate.html) subprocess  with `-d -u -t 2592000` arguments when entering `keep.presenting` mode, and terminates the subprocess when exiting the mode.

**How to check it?**:  There should be a subprocess visible when a lock is taken, but this is untested.

**Multiprocess safe?**: Not tested.

:::


::::




## General questions
**What if the process holding the lock dies?**: The lock is automatically removed. 

**How to use wakepy in tests / CI**: One problem with tests and/or CI systems is that many times the environment is different, and preventing system going to sleep works differently there. To fake a successful inhibit lock in tests, you may set an environment variable: `WAKEPY_FAKE_SUCCESS` to `yes`.