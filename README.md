![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/np-8/wakepy)&nbsp;![PyPI](https://img.shields.io/pypi/v/wakepy)&nbsp;![PyPI - Downloads](https://img.shields.io/pypi/dm/wakepy)&nbsp;![GitHub](https://img.shields.io/github/license/np-8/wakepy)

# ⏰😴 wakepy 

Simple cross-platform wakelock written in Python. Keeps your computer from going to sleep. 


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
```
python -m wakepy
```
Starts the program. While running, computer will not go to sleep. If battery is running out, your OS might force laptop to sleep.

### CLI 

```
python -m wakepy [-h] [-s]

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
The program uses the `systemctl mask` command to prevent all forms of sleep or hybernation when setting the keepawake, and unmasks the functions when unsetting keepawake. This command will remain active until keepawake is removed.  The flag cannot prevent sleeping from user interaction.  This action does require sudo privileges.

### Darwin (macOS)
The program calls the `caffeinate` command when setting keepawake, and sends a break key-command when unsetting.  The flag does not prevent the user from manually sleeping the system or terminating the caffeinate process.

# ⚖️ Pros and Cons
### 👑💯 Advantages of wakepy
- wakepy has zero (python) dependencies
- wakepy is simple and it has a little amount of code. You can read the whole source code quickly
- It has permissive MIT licence
- It is multiplatform
- You can use it directly from command line, or within your python scripts
### 🔍❕ Disadvantages / pitfalls with wakepy
- Currently multiprocessing is not well supported; the first function calling `unset_keepawake` or releasing the `keepawake` context manager will allow the PC to sleep even if you have called `set_keepawake` multiple times. For these kind of cases, perhaps an implementation making mouse movement or pressing keyboard keys would work better.
  
## Changelog 
- See [CHANGELOG.md](CHANGELOG.md)