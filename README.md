![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/np-8/wakepy)&nbsp;![PyPI](https://img.shields.io/pypi/v/wakepy)&nbsp;![PyPI - Downloads](https://img.shields.io/pypi/dm/wakepy)&nbsp;![GitHub](https://img.shields.io/github/license/np-8/wakepy)


# ⏰😴 wakepy 

Simple wakelock written in Python. Keeps your computer from going to sleep.
- Command line utility
- Can be added into your long running scripts

## Requirements
Wakepy is currently Windows only. Feel free to submit pull request(s) for other platforms.

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

## Set keepawake within a python script

```
from wakepy import set_keepawake, unset_keepawake

set_keepawake()
# do stuff that takes long time
unset_keepawake()
```

## Details

### Windows
The program simply calls the [SetThreadExecutionState](https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate?redirectedfrom=MSDN) with the `ES_SYSTEM_REQUIRED` flag, when setting the keepawake, and removes flag when unsetting. The flag cannot prevent sleeping if
- User closes the lid of their laptop
- User presses power button
- User selects *Sleep* from the Start menu.
