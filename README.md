![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/np-8/wakepy)&nbsp;![PyPI](https://img.shields.io/pypi/v/wakepy)&nbsp;![PyPI - Downloads](https://img.shields.io/pypi/dm/wakepy)&nbsp;![GitHub](https://img.shields.io/github/license/np-8/wakepy)

# ⏰😴 wakepy 

Simple cross-platform wakelock written in Python. Prevent your computer from going to sleep in the middle of a long running task, or starting a screensaver automatically.



#### Table of Contents
- [Installing](#installing)
- [Usage](#usage)
  - [Start from command line](#start-from-command-line)
  - [Set keepawake within a python script](#usage-within-a-python-script)
- [Details](#details)
- [Changelog](#changelog)

## Requirements
Wakepy currently supports 
- Windows
- Linux (with DBus or systemd)
- macOS

# Installing

#### (A) Windows, macOS and Linux (jeepney)
Note: On linux, this will install and use **[`jeepney`](https://jeepney.readthedocs.io/)** for DBus communication.
```
pip install wakepy
```
#### (B) Linux (systemd)

If you want to install wakepy on linux and do not want to use jeepney, or dbus-python but systemd, install wakepy with.
```
pip install --no-deps wakepy
```
Please note that this requires also `systemd` to be installed on your system, and usage of `systemd` requires sudo.

# Usage


## Wakepy Python API


### Option 1: Keep system running your programs
- In this mode, sleep/suspend is inhibited (not allowed), but system is allowed to switch display off and switch screenlock on normally.
- This is ideal mode for running a task that takes a long time (video editing, training machine learning model, scraping, ...).
```python
from wakepy import keep.running

with keep.running() as m:
  if not m.success:
    # Did not succeed inhibiting sleep. 
    # Tell it to the user?
  
  something_which_takes_long_time()
```
- **Note**: On Linux the `keep.running` currently actually does the same thing as `keep.presenting`; remember to lock the screen manually! (will be fixed in a future release)

  
### Option 2: Keep presenting content from your screen
- In this mode, sleep/suspend is inhibited (not allowed), like in the running mode. In addition, system is not allowed to switch screensaver or screenlock on.
- This is ideal for watching videos or presenting some content from the screen for a long time.

```python
from wakepy import keep.presenting

with keep.presenting() as m:
  if not m.success:
    # Did not succeed inhibiting screensaver.
    # Tell it to the user?

  something_which_needs_display_on()
```

## Wakepy Command Line Interface (CLI)
Running
```
wakepy 
```
or  
```
python -m wakepy
```
starts the program.  While running, computer will not go to sleep. If battery is running out, your OS might force laptop to sleep. 

### CLI arguments

```
wakepy [-h] [-k] [-p]

options:
  -h, --help               show this help message and exit
  -k, --keep-running       Keep programs running; inhibit automatic sleep/suspend. This
                           is used as a default if no modes are selected.
  -p, --presentation       Presentation mode; inhibit automatic sleep, screensaver and
                           screenlock
```



## Details

### wakepy.keep.running

#### General / All systems

**Does keep.running prevent manually putting system to sleep?** All the methods, if not otherwise specified, only prevent the *automatic, idle timer timeout based* sleeping, so it is still possible to put system to sleep by selecting Suspend/Sleep from a menu, closing the laptop lid or pressing a power key, for example. One exception is systemd mask method on Linux, which prevents suspend altogether.

**Can I lock my computer after entered `keep.running` mode?**: Yes, and you probably should, if you're not near your computer. The programs will continue execution regardless of the lock.


#### Windows

**How it works?**:  The [SetThreadExecutionState](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate?redirectedfrom=MSDN) is called with the `ES_CONTINUOUS` and  `ES_SYSTEM_REQUIRED` flags to acquire a lock when entering the context. On exit, these flags are removed.

**How to check it?**:   Run `powercfg -requests` in an elevated PowerShell.

**Multiprocess safe?**: Yes.



#### Linux

**How it works?**: Wakepy uses, depending on what is installed, either (in this order)
1. D-Bus to call `Inhibit` method of [`org.freedesktop.ScreenSaver`](https://people.freedesktop.org/~hadess/idle-inhibition-spec/re01.html) (try first using jeepney, and then using dbus-python)
3. `systemctl mask`

**Note**: Current D-Bus -based implementation prevents also screenlock/screensaver (remember to lock manually!)

**Note 2**: The systemd mask method will inhibit all forms of sleep (including hibernation and sleep initialized by the user). It will change global system settings, so if your process exits abruptly, you'll have to undo the change.

**How to check it?**:  For D-Bus  `org.freedesktop.ScreenSaver` based solution, there is no possibility to check it afterwards. You may monitor the call with [`dbus-monitor`](https://dbus.freedesktop.org/doc/dbus-monitor.1.html), though. For systemd mask based solution, you'll see that the Suspend option is removed from the menu altogether.

**What systems are supported?** For D-Bus `org.freedesktop.ScreenSaver` method, you have to use a Freedesktop-compliant Desktop Environment, for example GNOME or KDE. The list of supported systems will be expanded in the future. For systemd solution, any Linux running systemd works, but you need sudo.

**Multiprocess safe?**: DBus: yes, systemd mask: no.


#### Darwin (macOS)

**How it works?**: Wakepy launches a [`caffeinate`](https://ss64.com/osx/caffeinate.html) subprocess when setting keepawake, and terminates the subprocess when unsetting.

**How to check it?**:  There should be a subprocess visible when a lock is taken, but this is untested.

**Multiprocess safe?**: Not tested.

### wakepy.keep.presenting

#### General / All systems

**Does keep.presenting prevent manually putting system to sleep?** All the methods, if not otherwise specified, only prevent the *automatic, idle timer timeout based*  sleeping and screensaver/screenlock, so it is still possible to put system to sleep by selecting Suspend/Sleep from a menu, closing the laptop lid or pressing a power key, for example. It is also possible to manually start the screenlock/screensaver while presenting mode is on. 

**Is my computer locked automatically in `keep.presenting` mode?**: No. Entering a screenlock automatically would stop presenting the content. 

#### Windows

**How it works?**:   The [SetThreadExecutionState](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate?redirectedfrom=MSDN) is called with the `ES_CONTINUOUS`, `ES_SYSTEM_REQUIRED` and `ES_DISPLAY_REQUIRED` flags to acquire a lock when entering the context. On exit, these flags are removed.

**How to check it?**:   Run `powercfg -requests` in an elevated PowerShell.

**Multiprocess safe?**: Yes.

#### Darwin (macOS)

**How it works?**: Wakepy launches a [`caffeinate`](https://ss64.com/osx/caffeinate.html) subprocess  with `-d -u -t 2592000` arguments when entering `keep.presenting` mode, and terminates the subprocess when exiting the mode.

**How to check it?**:  There should be a subprocess visible when a lock is taken, but this is untested.

**Multiprocess safe?**: Not tested.


### General questions
**What if the process holding the lock dies?**: The lock is automatically removed. With one exception: Using systemd mask method on Linux, since it alters global system settings. That will not be used unless other methods fail and you're running the process with sudo.

**How to use wakepy in tests / CI**: One problem with tests and/or CI systems is that many times the environment is different, and preventing system going to sleep works differently there. To fake a succesful inhibit lock in tests, you may set an environment variable: `WAKEPY_FAKE_SUCCESS` to `yes`.


# ⚖️👑 Key selling points
- Wakepy supports multiple operating systems and desktop environments
- Wakepy has permissive MIT licence
- It has a simple command line interface and a python API
- Wakepy has very little python dependencies:
  - Zero if using Windows or macOS or Linux + systemd
  - One if using linux + [jeepney](https://jeepney.readthedocs.io/) or linux + [dbus-python](https://dbus.freedesktop.org/doc/dbus-python/).

## Changelog 
- See [CHANGELOG.md](CHANGELOG.md)
