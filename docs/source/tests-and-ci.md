# Wakepy in tests and CI

If you're using wakepy in Continuous Integration tests, note that typically CI is running on a system where there is no Desktop Environment available. In addition, the available services and executables might be different from the services and executables you have on your machine. For this reason, even if wakepy is able to activate a mode on your machine, it might not be able to do so in CI tests.

## WAKEPY_FAKE_SUCCESS
To force wakepy to fake a successful mode activation, you may set an environment variable `WAKEPY_FAKE_SUCCESS` to a *truthy value* like `1`. This makes wakepy to use a fake method to always guarantee a successful mode change. This works with any modes. The WAKEPY_FAKE_SUCCESS Method is tried *before* any other possible Methods, which guarantees that there will be no IO (except for the env var check), and no calling of any executables or 3rd party services when WAKEPY_FAKE_SUCCESS is used.

### tox configuration

If using [tox](https://tox.wiki/), use [`setenv`](https://tox.wiki/en/4.14.2/config.html#set_env) (aka. `set_env`) in your tox.ini:

```{code-block} ini
[testenv]
# ... other settings
setenv =
    WAKEPY_FAKE_SUCCESS = "yes"
```

### nox configuration

If using [nox](https://nox.thea.codes/), set the `WAKEPY_FAKE_SUCCESS` environment variable by adding the key-value pair to `session.env` in your noxfile.py. For example:

```{code-block} python
@nox.session
def tests(session):
    session.env["WAKEPY_FAKE_SUCCESS"] = "yes"
    # ... run tests
```


```{admonition} Truthy and falsy values
:class: info
Only `0`, `no` and `false` are considered as falsy values (case ignored). Any other value is considered truthy.
```


## DBUS_SESSION_BUS_ADDRESS

On Linux, wakepy uses D-Bus methods to inhibit screensaver or power management. Therefore, you need to have `DBUS_SESSION_BUS_ADDRESS` set to the session D-Bus address. This is usually automatically set, but test runners might drop out set environment variables.

To pass the `DBUS_SESSION_BUS_ADDRESS` with tox, one would use:

```{code-block} ini
[testenv]
# ... other settings
passenv =
    DBUS_SESSION_BUS_ADDRESS
```