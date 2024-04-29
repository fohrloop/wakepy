# Quickstart


## Requirements

### Python

- CPython 3.7 to 3.13

### Platform

Wakepy supports following platforms:

Windows
: Supports Windows XP to Windows 11 (client), Windows Server 2003 or higher (server)

MacOS
: Mac OS X 10.8 Mountain Lion (July 2012) or newer

Linux
: Distributions using [GNOME](https://en.wikipedia.org/wiki/GNOME) or any Desktop Environment that implements the [Freedesktop.org](https://en.wikipedia.org/wiki/Freedesktop.org) ScreenSaver interface (`org.freedesktop.ScreenSaver`).[^linux-support]

[^linux-support]: The Linux support is under active development. Target is to support at least GNOME, KDE, Xfce, Cinnamon, LXQt and MATE Desktop Environments.
## Installing

To install wakepy from PyPI, run

```{code-block} text
pip install wakepy
```

```{admonition} About dependencies
:class: note

Wakepy does not have python dependencies, except:
- On *Linux*, **[`jeepney`](https://jeepney.readthedocs.io/)** is currently required for DBus communication. This might change in the future.
- On Python *3.7*, the [typing-extensions](https://pypi.org/project/typing-extensions/) is required.

The dependencies will be automatically installed if required.
```

## Basic Usage

If you want to keep a long task running, but do not want to prevent screen from locking and/or blanking, you can use `keep.running` context manager. If you also want to prevent screen lock and screen blank, use `keep.presenting`:


::::{tab-set}

:::{tab-item} No screen required

```{code-block} python
from wakepy import keep

with keep.running():
    # Do something that takes a long time
```

:::

:::{tab-item} Screen required

```{code-block} python
from wakepy import keep

with keep.presenting():
    # Do something that takes a long time
```

:::

::::


```{admonition} Wakepy API is still experimental 🚧
:class: note

Since wakepy is still 0.x.x, the API might change without further notice from
one release to another. After that, breaking changes should occur only part of
a major release (e.g. 1.x.x -> 2.0.0). 
```

### Mode quick reference



| Wakepy mode              | keep.running | keep.presenting |
| ------------------------ | ------------ | --------------- |
| Sleep is prevented       | Yes          | Yes             |
| Screenlock is prevented  | No*          | Yes             |
| Screensaver is prevented | No*          | Yes             |



```{note}
The table above only considers the *automatic* actions (go to sleep, start screenlock, start screensaver), which are based on the *idle timer*; It is still possible to put system to sleep by selecting Suspend/Sleep from a menu, closing the laptop lid or pressing a power key, for example. It is also possible to manually lock the session/screen or start screensaver.
```



## Links
- GitHub: [github.com/fohrloop/wakepy](https://github.com/fohrloop/wakepy)
- PyPI: [pypi.org/project/wakepy](https://pypi.org/project/wakepy/)

```{toctree}
:hidden:
:maxdepth: 2
:numbered: -1
:titlesonly:

modes
methods-reference
api-reference
cli-api
```

```{toctree}
:hidden:
:caption: 'Advanced Usage:'
:maxdepth: 2
:numbered: -1
:titlesonly:

tests-and-ci
```


```{toctree}
:hidden:
:caption: 'Technical Details:'
:maxdepth: 2
:numbered: -1
:titlesonly:

wakepy-mode-lifecycle
test-manually
```

```{toctree}
:hidden:
:caption: 'Development:'
:maxdepth: 2
:numbered: -1
:titlesonly:

changelog
migration
```