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
- Linux (with `systemd`)
- macOS

Feel free to submit pull request(s) for other platforms.

# Installing


```
pip install wakepy
```

# Usage

## Start from command line
Running*
```
wakepy 
```
or  
```
python -m wakepy
```
starts the program.  While running, computer will not go to sleep. If battery is running out, your OS might force laptop to sleep.

<sup>\**needs wakepy >= 0.5.0*</sup>
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

*new in version 0.4.0*

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
The program uses DBus to prevent the system from suspending/sleeping. The flag cannot prevent sleeping from user interaction. This approach is multiprocessing-safe and doesn't need `sudo` privileges but might not be available on all systems.   
As a fallback the program uses the `systemctl mask` command to prevent all forms of sleep or hybernation (including sleep initialized by the user) when setting the keepawake, and unmasks the functions when unsetting keepawake. This command will remain active until `unset_keepawake` is called and is not multiprocessing-safe because the first process that releases the wakelock unmasks the functions and thus no longer prevents sleep. This action *does require sudo privileges*.

### Darwin (macOS)
The program launches a [`caffeinate`](https://ss64.com/osx/caffeinate.html) in a subprocess when setting keepawake, and terminates the subprocess when unsetting. This does not prevent the user from manually sleeping the system or terminating the caffeinate process.

### Summary table

|                                                              | Windows                                                                                                                                                                         | Linux                                                                                                                                                                                   | Mac                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| wakepy uses                                                  | [SetThreadExecutionState](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate?redirectedfrom=MSDN) with the `ES_SYSTEM_REQUIRED` flag | DBus Inhibit/UnInhibit or as a fallback `systemctl mask`                                                                                                                                | [`caffeinate`](https://ss64.com/osx/caffeinate.html) |
| sudo / admin needed?                                         | No                                                                                                                                                                              | No                                                                                                                                                                                      | No                                                   |
| `keep_screen_awake` option                                   | Optional<br>Default: `False`                                                                                                                                                    | Always `True`                                                                                                                                                                           | Optional<br>Default: `False`                         |
| When `keep_screen_awake = True`                              | Screen is kept awake. <br><br>Windows will not be locked automatically.                                                                                                         | Screen is kept awake.<br>Automatic locking: on some distros, depending on how the lock screen is implemented.                                                                           | Screen is kept awake.<br>Automatic locking = ?       |
| Multiprocessing support                                      | Yes                                                                                                                                                                             | Yes                                                                                                                                                                                     | No                                                   |
| When process calling `set_keepawake` dies                    | All flags set by the process are removed. See: [ How will killing while lock set affect it?](https://github.com/np-8/wakepy/issues/16)                                          | The wakelock is immediately released except if the `systemctl mask` fallback is used, in which case the wakelock will be held even over a reboot until it's released.                   | Nothing happens                                      |
| How to debug or see the changes<br>done by wakepy in the OS? | Run `powercfg -requests` in<br>elevated PowerShell                                                                                                                              | ?<br>If the `systemctl mask` fallback is used, run `sudo systemctl status sleep.target suspend.target hibernate.target hybrid-sleep.target` in Terminal.                                | ?                                                    |
| If on laptop, and battery low?                               | Sleep                                                                                                                                                                           | Default 'when battery low' action will be triggered.<bt>If the `systemctl mask` fallback is used, most distros will do their set 'when battery low' action but fail if that is suspend. | ?                                                    |

# ⚖️ Pros and Cons
### 👑💯 Advantages of wakepy
- wakepy has zero (python) dependencies
- wakepy is simple and it has a little amount of code. You can read the whole source code quickly
- It has permissive MIT licence
- It is multiplatform
- You can use it directly from command line, or within your python scripts
- It runs without admin/sudo priviledges on Windows and Mac. 
### 🔍❕ Disadvantages / pitfalls with wakepy
- On Linux, if DBus unavailable, the fallback solution using `systemctl` needs sudo priviledges.
- Currently multiprocessing is not well supported on Mac (?); the first function calling `unset_keepawake` or releasing the `keepawake` context manager will allow the PC to sleep even if you have called `set_keepawake` multiple times. For these kind of cases, perhaps an implementation making mouse movement or pressing keyboard keys would work better.
## Changelog 
- See [CHANGELOG.md](CHANGELOG.md)
