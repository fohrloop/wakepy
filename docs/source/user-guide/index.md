# User Guide

```{toctree}
:hidden:

modes
tests-and-ci
technical-details
```

## Requirements

Wakepy supports Windows, MacOS and Linux flavours which Desktop Environment that implements the `org.freedesktop.ScreenSaver` interface[^linux-support].

[^linux-support]: The Linux support is under active development. Target is to support at least GNOME, KDE, Xfce, Cinnamon, LXQt and MATE Desktop Environments. 
## Installing

To install wakepy from PyPI, run
```
pip install wakepy
```

```{note}
On Linux will install also **[`jeepney`](https://jeepney.readthedocs.io/)** for DBus communication (if not installed). On other systems there are no python requirements.
```

## Quick Start

If you want to keep a long task running, but do not want to prevent screen from locking and/or blanking, you can use `keep.running` context manager. If you also want to prevent screen lock and screen blank, use `keep.presenting`:


::::{tab-set}

:::{tab-item} No screen required

```{code-block} python
from wakepy import keep

with keep.running() as k:
    # Do something that takes a long time
```

:::

:::{tab-item} Screen required

```{code-block} python
from wakepy import keep

with keep.presenting() as k:
    # Do something that takes a long time
```

:::

::::


### Mode quick reference 
 


| Wakepy mode              | keep.running | keep.presenting |
| ------------------------ | ------------ | --------------- |
| Sleep is prevented       | Yes          | Yes             |
| Screenlock is prevented  | No*          | Yes             |
| Screensaver is prevented | No*          | Yes             |

```{warning}
*On Linux, on wakepy <= 0.7.0 the default behavior with keep.running is to also prevent automatic screenlock! This is because `org.freedesktop.ScreenSaver.Inhibit` method is used. This will be changed in a future release.
```

```{note}
The table above only considers the *automatic* actions (go to sleep, start screenlock, start screensaver), which are based on the *idle timer*; It is still possible to put system to sleep by selecting Suspend/Sleep from a menu, closing the laptop lid or pressing a power key, for example. It is also possible to manually lock the session/screen or start screensaver.
```

