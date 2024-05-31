# Overview

## What is wakepy?

Wakepy is a package with an Python API and a CLI tool for *keeping a system awake*. Namely:

⌛ **Keeping CPU awake**:  For long running tasks. Inhibit the automatic, timer based sleep or suspend action, but allow screenlock and screensaver turning on and monitor turning off. (See: <a href="https://wakepy.readthedocs.io/stable/modes.html#keep-running-mode">keep.running</a>)

🖥️ **Keeping screen awake**:  For long running tasks which require also the screen on and screenlock and screensaver inhibited. (See: <a href="https://wakepy.readthedocs.io/stable/modes.html#keep-presenting-mode">keep.presenting</a>)


## Supported platforms

Wakepy may keep the following systems awake. ⌛: <a href="https://wakepy.readthedocs.io/stable/modes.html#keep-running-mode">keep.running</a> mode, 🖥️:<a href="https://wakepy.readthedocs.io/stable/modes.html#keep-presenting-mode">keep.presenting</a> mode.


<table class="wakepy-table">
  <colgroup>
    <col style="width: 18%;">
    <col style="width: 68%;">
    <col style="width: 14%;">
  </colgroup>
  <thead>
    <tr>
      <th>Platform</th>
      <th>Methods</th>
      <th>Modes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Windows<sup>[1]</sup></td>
      <td><a href="https://wakepy.readthedocs.io/stable/methods-reference.html#setthreadexecutionstate">SetThreadExecutionState</a></td>
      <td>⌛ 🖥️</td>
    </tr>
    <tr>
    </tr>
    <tr>
      <td>macOS<sup>[2]</sup></td>
      <td><a href="https://wakepy.readthedocs.io/stable/methods-reference.html#macos-caffeinate">caffeinate</a></td>
      <td>⌛ 🖥️</td>
    </tr>
    <tr>
      <td><a href="https://en.wikipedia.org/wiki/GNOME">GNOME</a><sup>[3]</sup></td>
      <td><a href="https://wakepy.readthedocs.io/stable/methods-reference.html#org-gnome-sessionmanager">org.gnome.SessionManager</a><br>
      <a href="https://wakepy.readthedocs.io/stable/methods-reference.html#org-freedesktop-screensaver">org.freedesktop.ScreenSaver</a></td>
      <td>⌛ 🖥️</td>
    </tr>
    <tr>
      <td><a href="https://en.wikipedia.org/wiki/KDE_Plasma">KDE Plasma</a><sup>[4]</sup></td>
      <td><a href="https://wakepy.readthedocs.io/stable/methods-reference.html#org-freedesktop-powermanagement">org.freedesktop.PowerManagement</a><br>
      <a href="https://wakepy.readthedocs.io/stable/methods-reference.html#org-freedesktop-screensaver">org.freedesktop.ScreenSaver</a></td>
      <td>⌛ 🖥️</td>
    </tr>
    <tr>
      <td><a href="https://en.wikipedia.org/wiki/Freedesktop.org">Freedesktop.org</a><sup>[5]</sup></td>
      <td>
      <a href="https://wakepy.readthedocs.io/stable/methods-reference.html#org-freedesktop-powermanagement">org.freedesktop.PowerManagement</a><br>
      <a href="https://wakepy.readthedocs.io/stable/methods-reference.html#org-freedesktop-screensaver">org.freedesktop.ScreenSaver</a>
      </td>
      <td>⌛ 🖥️</td>
    </tr>
  </tbody>
</table>


## Installing

Wakepy supports CPython 3.7 to 3.13, and may be installed with

```
pip install wakepy
```

To get the `wakepy` [CLI command](#cli-api) working, you might need to restart the shell / terminal application.

## Why wakepy?
Here's some reasons why you might want to consider using wakepy:

🛡️ For security reasons
: When you don't want to use a technique which keeps the screen awake and disables the automatic screen lock. I.e. you *only* want to disable the automatic suspend. 

🦸 You need a cross-platform solution
: Same code works on Windows, macOS and Linux.

⚙️ You want to have more control
: It is possible to whitelist or blacklist the used wakepy Methods. It is also possible to prioritize them and define a on-fail action in case activating a wakepy mode fails.

✂️ You want to keep the amount of dependencies low
: If you're running wakepy on Linux,  [jeepney](https://jeepney.readthedocs.io/) is required for D-Bus based methods. On Python 3.7,  [typing-extensions](https://pypi.org/project/typing-extensions/) is needed for typing. Otherwise: wakepy has no python dependencies.

⚖️ Package needs to have a permissive licence
: Wakepy is licenced under permissive [MIT License](https://github.com/fohrloop/wakepy/blob/main/LICENSE.txt).



## Command line interface (CLI)

To keep system from sleeping, run

```
wakepy
```

For presentation mode, add `-p` flag. See also: [CLI API](#cli-api)

## Basic usage within Python

In the simplest case, keeping a system running long running task with wakepy would be in python (See: [`keep.running`](#keep-running-mode)):

```{code-block} python
from wakepy import keep

with keep.running():
    # Do something that takes a long time. The system may start screensaver
    # / screenlock or blank the screen, but CPU will keep running.
```

If you want to *also* prevent screen lock and screen blank, use the [`keep.presenting`](#keep-presenting-mode) mode:


```{code-block} python
from wakepy import keep

with keep.presenting():
    # Do something that takes a long time and requires the screen to be awake
```


```{admonition} Next Steps
:class: seealso

See the [User Guide](#user-guide) and the available wakepy [Modes](#wakepy-modes) and [Methods](#wakepy-methods)
```
```{admonition} Wakepy API is still experimental 🚧
:class: note

Since wakepy is still 0.x.x, the API might change without further notice from
one release to another. After that, breaking changes should occur only part of
a major release (e.g. 1.x.x -> 2.0.0). 
```


## Where wakepy is used?

- [viskillz-blender](https://github.com/viskillz/viskillz-blender) — Generating assets of Mental Cutting Test exercises
- [mpc-autofill](https://github.com/chilli-axe/mpc-autofill) — Automating MakePlayingCards' online ordering system
- [lakeshorecryotronics/python-driver](https://github.com/lakeshorecryotronics/python-driver) — Lake Shore instruments python Driver
- [UCSD-E4E/baboon-tracking](https://github.com/UCSD-E4E/baboon-tracking) — In pipelines of a Computer Vision project tracking baboons
- [davlee1972/upscale_video](https://github.com/davlee1972/upscale_video) — Upscaling video using AI
- [minarca](https://github.com/ikus060/minarca) — Cross-platform data backup software



## Links
- GitHub: [github.com/fohrloop/wakepy](https://github.com/fohrloop/wakepy)
- PyPI: [pypi.org/project/wakepy](https://pypi.org/project/wakepy/)

---------------

| Footnotes                                                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------------- |
| <sup>[1]</sup> Windows XP or higher. Windows Server 2003 or higher.                                                          |
| <sup>[2]</sup> Mac OS X 10.8 Mountain Lion (July 2012) or newer.                                                                            |
| <sup>[3]</sup> GNOME 2.24 (Sept 2008) onwards.                                                                                              |
| <sup>[4]</sup> KDE Plasma 5.12.90 (May 2018) onwards.                                                                                       |
| <sup>[5]</sup> Freedesktop.org compliant Desktop Environments on Unix-line (Linux/BSD) system which implements the listed D-Bus interfaces. |



```{toctree}
:hidden:
:maxdepth: 2
:numbered: -1
:titlesonly:

user-guide
tests-and-ci
```

```{toctree}
:hidden:
:caption: 'Reference Manual:'
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