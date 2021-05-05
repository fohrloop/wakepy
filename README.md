![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/np-8/wakepy)&nbsp;![PyPI](https://img.shields.io/pypi/v/wakepy)&nbsp;![PyPI - Downloads](https://img.shields.io/pypi/dm/wakepy)&nbsp;![GitHub](https://img.shields.io/github/license/np-8/wakepy)


# ⏰😴 wakepy 

Simple wakelock written in Python. Keeps your computer from going to sleep.
- Command line utility
- Can be added into your long running scripts

## Requirements
<<<<<<< HEAD
Wakepy currently supports both Windows and Linux. Feel free to submit pull request(s) for other platforms.
=======
Wakepy currently supports Windows and Darwin operating systems. Feel free to submit pull request(s) for other platforms.
>>>>>>> Add darwin support

# Installing


```
pip install wakepy
```

# Usage

## Start from command line
```
python -m wakepy
```
Starts the program. While running, computer will not go to sleep. If battery running out, Windows might force laptop to sleep.

### CLI 

```
usage: wakepy [-h] [-s]

optional arguments:
  -h, --help            show this help message and exit
  -s, --keep-screen-awake
                        Keep also the screen awake.
```

## Set keepawake within a python script

```python
from wakepy import set_keepawake, unset_keepawake

set_keepawake(keep_screen_awake=False)
# do stuff that takes long time
unset_keepawake()
```
### Parameters
-  `keep_screen_awake` can be used to keep also the screen awake. The default is `False`.

## Details

### Windows
The program simply calls the [SetThreadExecutionState](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate?redirectedfrom=MSDN) with the `ES_SYSTEM_REQUIRED` flag, when setting the keepawake, and removes flag when unsetting. The flag cannot prevent sleeping if
- User presses power button
- User selects *Sleep* from the Start menu.

### Linux
The program uses the `systemctl mask` command to prevent all forms of sleep or hybernation when setting the keepawake, and unmasks the functions when unsetting keepawake. This command will remain active until keepawake is removed.  The flag cannot prevent sleeping from user interaction.  This action does require sudo privilages.

### Darwin
The program calls the `caffeinate` command when setting keepawake, and sends a break key-command when unsetting.  The flag does not prevent the user from manually sleeping the system or terminating the caffeinate process.

