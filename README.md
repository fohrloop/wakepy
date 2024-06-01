![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/fohrloop/wakepy)&nbsp;![PyPI](https://img.shields.io/pypi/v/wakepy)&nbsp;![PyPI - Downloads](https://img.shields.io/pypi/dm/wakepy)&nbsp;![GitHub](https://img.shields.io/github/license/fohrloop/wakepy)

# ⏰😴 wakepy

Cross-platform wakelock / keep-awake / stay-awake written in Python.

<!-- start wakepy readme main -->

## What is wakepy?

Wakepy is a package with an Python API and a CLI tool for *keeping a system awake*. It has two main modes:

⌛ **Keeping CPU awake**:  For long running tasks. Inhibit the automatic, timer based sleep or suspend action, but allow screenlock and screensaver turning on and monitor turning off. *E.g.* for training machine learning models, video encoding and web scraping. (See: <a href="https://wakepy.readthedocs.io/stable/modes.html#keep-running-mode"><b><code>keep.running</code></b></a>)

🖥️ **Keeping screen awake**:  For long running tasks which require also the screen on and screenlock and screensaver inhibited.  *E.g.* for showing a video and dashboard / monitoring apps. (See: <a href="https://wakepy.readthedocs.io/stable/modes.html#keep-presenting-mode"><b><code>keep.presenting</code></b></a>)

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

To get the `wakepy` <a href="https://wakepy.readthedocs.io/stable/cli-api.html">CLI command</a> working, you might need to restart the shell / terminal application.

## Why wakepy?
Here's some reasons why you might want to consider using wakepy:


<dl>
  <dt>🛡️ For security reasons</dt>
  <dd>When you don't want to use a technique which keeps the screen awake and disables the automatic screen lock. I.e. you *only* want to disable the automatic suspend.</dd>
  <dt>🦸 You need a cross-platform solution</dt>
  <dd>Same code works on Windows, macOS and Linux.</dd>
  <dt>⚙️ You want to have more control</dt>
  <dd>It is possible to whitelist or blacklist the used wakepy Methods. It is also possible to prioritize them and define a on-fail action in case activating a wakepy mode fails.</dd>
  <dt>✂️ You want to keep the amount of dependencies low</dt>
  <dd>If you're running wakepy on Linux,  <a href="https://jeepney.readthedocs.io/">jeepney</A> is required for D-Bus based methods. On Python 3.7,  <a href="https://pypi.org/project/typing-extensions/">typing-extensions</a> is needed for typing. Otherwise: wakepy has no python dependencies.</dd>
  <dt>⚖️ Package needs to have a permissive licence</dt>
  <dd>Wakepy is licenced under permissive <a href="https://github.com/fohrloop/wakepy/blob/main/LICENSE.txt">MIT License</a>.</dd>
</dl>


## Command line interface (CLI)

To keep system from sleeping, run

```
wakepy
```

For presentation mode, add `-p` flag. See also: <a href="https://wakepy.readthedocs.io/stable/cli-api.html">CLI API</a>.

## Basic usage within Python

In the simplest case, keeping a system running long running task with wakepy would be in python (See: <a href="https://wakepy.readthedocs.io/stable/modes.html#keep-running-mode">keep.running</a>):


```python
from wakepy import keep

with keep.running():
    # Do something that takes a long time. The system may start screensaver
    # / screenlock or blank the screen, but CPU will keep running.
```


If you want to *also* prevent screen lock and screen blank, use the <a href="https://wakepy.readthedocs.io/stable/modes.html#keep-presenting-mode">keep.presenting</a>mode:


```{code-block} python
from wakepy import keep

with keep.presenting():
    # Do something that takes a long time and requires the screen to be awake
```

<!-- end wakepy readme main -->

> [!TIP]
> See the [User Guide](#user-guide) and the available wakepy [Modes](#wakepy-modes) and [Methods](#wakepy-methods)

> [!NOTE]
> Wakepy API is still experimental 🚧
> 
> Since wakepy is still 0.x.x, the API might change without further notice from
> one release to another. After that, breaking changes should occur only part of
> a major release (e.g. 1.x.x -> 2.0.0).

<!-- start wakepy readme part2 -->
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
- Documentation: [wakepy.readthedocs.io/stable](https://wakepy.readthedocs.io/stable)
- Changelog: [wakepy.readthedocs.io/stable/changelog.html](https://wakepy.readthedocs.io/stable/changelog.html)



---------------

| Footnotes                                                                                                                    |
| ---------------------------------------------------------------------------------------------------------------------------- |
| <sup>[1]</sup> Windows XP or higher. Windows Server 2003 or higher.                                                          |
| <sup>[2]</sup> Mac OS X 10.8 Mountain Lion (July 2012) or newer.                                                                            |
| <sup>[3]</sup> GNOME 2.24 (Sept 2008) onwards.                                                                                              |
| <sup>[4]</sup> KDE Plasma 5.12.90 (May 2018) onwards.                                                                                       |
| <sup>[5]</sup> Freedesktop.org compliant Desktop Environments on Unix-line (Linux/BSD) system which implements the listed D-Bus interfaces. |

<!-- end wakepy readme part2 -->

