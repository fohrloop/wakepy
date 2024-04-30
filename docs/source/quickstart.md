# Quickstart


## Installing

To install wakepy from PyPI, run

```{code-block} text
pip install wakepy
```

## Basic Usage

If you want to keep a long task running, but do not want to prevent screen from locking and/or blanking, you can use the [`keep.running`](#keep-running-mode) context manager. If you also want to prevent screen lock and screen blank, use [`keep.presenting`](#keep-presenting-mode):


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



