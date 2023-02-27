![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/np-8/wakepy)&nbsp;![PyPI](https://img.shields.io/pypi/v/wakepy)&nbsp;![PyPI - Downloads](https://img.shields.io/pypi/dm/wakepy)&nbsp;![GitHub](https://img.shields.io/github/license/np-8/wakepy)

# ⏰😴 wakepy 

Simple cross-platform wakelock written in Python. Prevent your computer from going to sleep in the middle of a long running task. 


#### Table of Contents
- [Installing](#installing)
- [Usage](#usage)
  - [Start from command line](#start-from-command-line)
  - [Set keepawake within a python script](#set-keepawake-within-a-python-script)
- [Details](#details)
- [Changelog](#changelog)

## Requirements
Wakepy currently supports 
- Windows
- Linux (with DBus or systemd)
- macOS

Feel free to submit pull request(s) for other platforms.

# Installing

#### (A) Windows, macOS and Linux (jeepney)
Note: On linux, this will install and use **[`jeepney`](https://jeepney.readthedocs.io/)** for DBus communication.
```
pip install wakepy
```
#### (B) Linux (dbus-python)

If you want to install wakepy on linux and do not want to use jeepney, but **[`dbus-python`](https://dbus.freedesktop.org/doc/dbus-python/)**, the official libdbus (aka. `dbus`) Python binding, use   
```
pip install --no-deps wakepy
pip install dbus-python
```
Please note that this requires also `libdbus` to be installed on your system. Some linux distributions come with `dbus-python`.

#### (C) Linux (systemd)

If you want to install wakepy on linux and do not want to use jeepney, or dbus-python but systemd, install wakepy with.
```
pip install --no-deps wakepy
```
Please note that this requires also `systemd` to be installed on your system, and usage of `systemd` requires sudo.

# Usage

## Start from command line
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
wakepy [-h] [-s]

optional arguments:    
  -h, --help               show this help message and exit
  -s, --keep-screen-awake  Keep also the screen awake. On Linux, this flag is set on and cannot be disabled.
```

## Usage within a python script

### Option 1: `set_keepawake` and `unset_keepawake` functions

```python
from wakepy import set_keepawake, unset_keepawake

set_keepawake(keep_screen_awake=False)
# do stuff that takes long time
unset_keepawake()
```
### Option 2: `keepawake` context manager


```python
from wakepy import keepawake

with keepawake(keep_screen_awake=False):
  ... # do stuff that takes long time
```

### Parameters
-  `keep_screen_awake` can be used to keep also the screen awake. The default is `False`. On Linux, this is set to `True` and cannot be changed.

## Details

### Windows
The program simply calls the [SetThreadExecutionState](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate?redirectedfrom=MSDN) with the `ES_SYSTEM_REQUIRED` flag, when setting the keepawake, and removes flag when unsetting. The flag cannot prevent sleeping if
- User presses power button
- User selects *Sleep* from the Start menu.

### Linux
The program uses, depending on what is installed, either (in this order)
1. jeepney (pure python dbus implementation. Default)
2. dbus-python (requires libdbus)
3. `systemctl mask`

The first two options will use DBus to call the inhibit method of `org.freedesktop.ScreenSaver`, which will prevent the system from suspending/speeling. The inhibit will be released when the process dies or when unset_keepawake is called. The flag cannot prevent sleeping from user interaction. This approach is multiprocessing-safe and doesn't need `sudo` privileges but you have to use a Freedesktop-compliant desktop environment, for example GNOME, KDE or Xfce. See full list in [the freedesktop.org wiki](https://freedesktop.org/wiki/Desktops/). 

The `systemctl mask` command will prevent all forms of sleep or hibernation (including sleep initialized by the user) when calling `set_keepawake`, and unmasks the functions when calling `unset_keepawake`. This command will remain active until `unset_keepawake` is called and is not multiprocessing-safe because the first process that releases the wakelock unmasks the functions and thus no longer prevents sleep.  *Using systemd requires sudo privileges*.


### Darwin (macOS)
The program launches a [`caffeinate`](https://ss64.com/osx/caffeinate.html) in a subprocess when setting keepawake, and terminates the subprocess when unsetting. This does not prevent the user from manually sleeping the system or terminating the caffeinate process.

### Summary table

|                                                              | Windows                                                                                                                                                                         | Linux                                                                                                                                                                                   | Mac                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| wakepy uses                                                  | [SetThreadExecutionState](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate?redirectedfrom=MSDN) with the `ES_SYSTEM_REQUIRED` flag | DBus Inhibit/UnInhibit or as a fallback `systemctl mask`                                                                                                                                | [`caffeinate`](https://ss64.com/osx/caffeinate.html) |
| sudo / admin needed?                                         | No                                                                                                                                                                              | No           (with dbus) / Yes (systemd)                                                                                                                                                                           | No                                                   |
| `keep_screen_awake` option                                   | Optional<br>Default: `False`                                                                                                                                                    | Always `True`                                                                                                                                                                           | Optional<br>Default: `False`                         |
| When `keep_screen_awake = True`                              | Screen is kept awake. <br><br>Windows will not be locked automatically.                                                                                                         | Screen is kept awake.<br>Automatic locking: on some distros, depending on how the lock screen is implemented.                                                                           | Screen is kept awake.<br>Automatic locking = ?       |
| Multiprocessing support                                      | Yes                                                                                                                                                                             | Yes       (dbus) / No (systemd)                                                                                                                                                                              | No                                                   |
| When process calling `set_keepawake` dies                    | All flags set by the process are removed. See: [ How will killing while lock set affect it?](https://github.com/np-8/wakepy/issues/16)                                          | The wakelock is immediately released except if the `systemctl mask` fallback is used, in which case the wakelock will be held even over a reboot until it's released.                   | Nothing happens                                      |
| How to debug or see the changes<br>done by wakepy in the OS? | Run `powercfg -requests` in<br>elevated PowerShell                                                                                                                              | ?<br>If the `systemctl mask` fallback is used, run `sudo systemctl status sleep.target suspend.target hibernate.target hybrid-sleep.target` in Terminal.                                | ?                                                    |
| If on laptop, and battery low?                               | Sleep                                                                                                                                                                           | Default 'when battery low' action will be triggered.<bt>If the `systemctl mask` fallback is used, most distros will do their set 'when battery low' action but fail if that is suspend. | ?                                                    |

# ⚖️ Pros and Cons
### 👑💯 Advantages of wakepy
- wakepy has very little python dependencies:
  - Zero if using Windows or macOS or Linux + systemd
  - One if using linux + [jeepney](https://jeepney.readthedocs.io/) or linux + [dbus-python](https://dbus.freedesktop.org/doc/dbus-python/).
- wakepy is simple and it has a little amount of code. You can read the whole source code quickly
- It has permissive MIT licence
- It is multiplatform
- You can use it directly from command line, or within your python scripts
- It runs without admin/sudo priviledges on Windows and Mac and Linux (with DBus)!
### 🔍❕ Disadvantages / pitfalls with wakepy
- On Linux, if DBus unavailable, the fallback solution using `systemctl` needs sudo priviledges.
- Currently multiprocessing is not well supported on Mac (?); the first function calling `unset_keepawake` or releasing the `keepawake` context manager will allow the PC to sleep even if you have called `set_keepawake` multiple times. 
## Changelog 
- See [CHANGELOG.md](CHANGELOG.md)
