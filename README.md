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
The program uses the `systemctl mask` command to prevent all forms of sleep or hybernation when setting the keepawake, and unmasks the functions when unsetting keepawake. This command will remain active until keepawake is removed.  The flag cannot prevent sleeping from user interaction.  This action *does require sudo privileges*.

### Darwin (macOS)
The program launches a [`caffeinate`](https://ss64.com/osx/caffeinate.html) in a subprocess when setting keepawake, and terminates the subprocess when unsetting. This does not prevent the user from manually sleeping the system or terminating the caffeinate process.

### Summary table

|                                                              | Windows                                                                                                                                                                         | Linux                                                                                                                                                                                 | Mac                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| wakepy uses                                                  | [SetThreadExecutionState](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate?redirectedfrom=MSDN) with the `ES_SYSTEM_REQUIRED` flag | `systemctl mask`                                                                                                                                                                      | [`caffeinate`](https://ss64.com/osx/caffeinate.html) |
| sudo / admin needed?                                         | No                                                                                                                                                                              | Yes                                                                                                                                                                                   | No                                                   |
| `keep_screen_awake` option                                   | Optional<br>Default: `False`                                                                                                                                                    | Always `True`                                                                                                                                                                         | Optional<br>Default: `False`                         |
| When `keep_screen_awake = True`                              | Screen is kept awake. <br><br>Windows will not be locked automatically.                                                                                                         | Screen is kept awake.<br>Automatic locking: on some distros, depending on how the lock screen is implemented.                                                                         | Screen is kept awake.<br>Automatic locking = ?       |
| Multiprocessing support                                      | Yes                                                                                                                                                                             | No                                                                                                                                                                                    | No                                                   |
| When process calling `set_keepawake` dies                    | All flags set by the process are removed. See: [ How will killing while lock set affect it?](https://github.com/np-8/wakepy/issues/16)                                          | The wakelock is held even over a reboot until `unset_keepawake` is called or `sleep.target`, `suspend.target`, `hibernate.target` and `hybrid-sleep.target` are unmasked otherwise.   | Nothing happens                                      |
| How to debug or see the changes<br>done by wakepy in the OS? | Run `powercfg -requests` in<br>elevated PowerShell                                                                                                                              | run `sudo systemctl status sleep.target suspend.target hibernate.target hybrid-sleep.target` in Terminal and see if the "Loaded" status for the units is set to "masked" or "loaded". | ?                                                    |
| If on laptop, and battery low?                               | Sleep                                                                                                                                                                           | Most distros will (or if set to "suspend", attempt to) do their set "when battery low" action, if that is set to none they will just crash as soon as the battery becomes too weak.   | ?                                                    |

# ⚖️ Pros and Cons
### 👑💯 Advantages of wakepy
- wakepy has zero (python) dependencies
- wakepy is simple and it has a little amount of code. You can read the whole source code quickly
- It has permissive MIT licence
- It is multiplatform
- You can use it directly from command line, or within your python scripts
- It runs without admin/sudo priviledges on Windows and Mac. 
### 🔍❕ Disadvantages / pitfalls with wakepy
- On Linux, the current solution using `systemctl` needs sudo priviledges. PRs to circumvent this are welcome.
- Currently multiprocessing is not well supported on Mac and Linux (?); the first function calling `unset_keepawake` or releasing the `keepawake` context manager will allow the PC to sleep even if you have called `set_keepawake` multiple times. For these kind of cases, perhaps an implementation making mouse movement or pressing keyboard keys would work better.
## Changelog 
- See [CHANGELOG.md](CHANGELOG.md)
