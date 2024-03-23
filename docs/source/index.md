# Quickstart


## Requirements

Wakepy supports Windows, MacOS and Linux flavours which Desktop Environment that implements the `org.freedesktop.ScreenSaver` interface[^linux-support].

[^linux-support]: The Linux support is under active development. Target is to support at least GNOME, KDE, Xfce, Cinnamon, LXQt and MATE Desktop Environments.
## Installing

To install wakepy from PyPI, run

```{code-block} text
pip install wakepy
```

```{note}
On Linux will install also **[`jeepney`](https://jeepney.readthedocs.io/)** for DBus communication (if not installed). On other systems there are no python requirements.

On Python 3.7 installs [typing-extensions](https://pypi.org/project/typing-extensions/).
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