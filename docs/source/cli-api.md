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
wakepy [-h] [-k] [-p]

options:
  -h, --help               show this help message and exit
  -k, --keep-running       Keep programs running; inhibit automatic sleep/suspend. This
                           is used as a default if no modes are selected.
  -p, --presentation       Presentation mode; inhibit automatic sleep, screensaver and
                           screenlock
```