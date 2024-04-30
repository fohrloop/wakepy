# Overview

## What is wakepy?

Wakepy is a package with an Python API and a CLI tool for *keeping a system awake*. Namely:

⌛ **Keeping CPU awake**:  For long running tasks. Inhibit the automatic, timer based sleep or suspend action, but allow screenlock and screensaver turning on and monitor turning off. (See: [keep.running](#keep-running-mode))

🖥️ **Keeping screen awake**:  For long running tasks which require also the screen on and screenlock and screensaver inhibited. (See: [keep.presenting](#keep-presenting-mode))


## Supported platforms

Wakepy may keep the following systems awake:


<table class="wakepy-table">
  <colgroup>
    <col style="width: 25%;">
    <col style="width: 75%;">
  </colgroup>
  <thead>
    <tr>
      <th>Platform</th>
      <th>Details</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="hoverable" rowspan="2">Windows</td>
      <td>Windows XP to Windows 11</td>
    </tr>
    <tr>
      <td>Windows Server 2003 or higher</td>
    </tr>
    <tr>
      <td>Mac OS</td>
      <td>Mac OS X 10.8 Mountain Lion (July 2012) or newer</td>
    </tr>
    <tr>
      <td class="hoverable" rowspan="2">Linux
      <a class="footnote-reference brackets" href="#linux-support" id="linux-support-note" role="doc-noteref"><span class="fn-bracket">[</span>1<span class="fn-bracket">]</span></a></td>
      <td>Distributions using <a href="https://en.wikipedia.org/wiki/GNOME">GNOME</a></td>
    </tr>
    <tr>
      <td>Desktop Environments which implement the <a href="https://en.wikipedia.org/wiki/Freedesktop.org">Freedesktop.org</a> ScreenSaver interface (<code>org.freedesktop.ScreenSaver</code>)</td>
    </tr>
  </tbody>
</table>

<aside class="footnote brackets" id="linux-support" role="doc-footnote">
<span class="label"><span class="fn-bracket">[</span><a role="doc-backlink" href="#linux-support-note  ">1</a><span class="fn-bracket">]</span></span>
<p>The Linux support is under active development. Target is to support at least GNOME, KDE, Xfce, Cinnamon, LXQt and MATE Desktop Environments.</p>
</aside>

## Installing

Wakepy supports CPython 3.7 to 3.13, and may be installed with

```
pip install wakepy
```

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

```{toctree}
:hidden:
:maxdepth: 2
:numbered: -1
:titlesonly:

quickstart
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