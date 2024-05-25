# Quickstart

## Installing

To install wakepy from PyPI, run

```{code-block} text
pip install wakepy
```


## Command line interface (CLI)

To keep system from sleeping, run

```
wakepy
```

For presentation mode, add `-p` flag. See also: [CLI API](#cli-api)

## Keeping the system on with wakepy (Python)

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



```{admonition} Wakepy API is still experimental 🚧
:class: note

Since wakepy is still 0.x.x, the API might change without further notice from
one release to another. After that, breaking changes should occur only part of
a major release (e.g. 1.x.x -> 2.0.0). 
```






