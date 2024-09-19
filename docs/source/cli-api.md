# CLI API

It is possibe to start wakepy from the command line either by running

```{code-block} text
wakepy
```

or

```{code-block} text
python -m wakepy
```

This starts wakepy in the *default mode* (`-k`), which corresponds to a call to `keep.running` with default arguments. The available options are:

```{code-block} output
wakepy [-h | -r | -p]

options:
  -h, --help               show this help message and exit
  -r, --keep-running       Keep programs running; inhibit automatic sleep/suspend. This
                           is used as a default if no modes are selected.
  -p, --keep-presenting    Presentation mode; inhibit automatic sleep, screensaver and
                           screenlock
```


````{admonition} Command "wakepy" not found?
:class: note

If you just installed `wakepy`, you might need to restart shell / terminal application to make added to the PATH.
````

```{versionchanged} 0.10.0
Renamed `-k` to `-r` and `--presentation` to `--keep-presenting` ([wakepy/#355](https://github.com/fohrloop/wakepy/issues/355)).
```