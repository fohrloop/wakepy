# Wakepy in tests and CI

If you're using wakepy in Continuous Integration tests, note that typically CI is running on a system where there is no Desktop Environment available. In addition, the available services and executables might be different from the services and executables on the machine where the code using wakepy is meant to be running. For this reason, even if wakepy is able to activate a mode on your development machine, it might not be able to do so in CI tests. *In most cases it is recommended to make wakepy always succeed in the mode activation in unit tests and CI by setting the `WAKEPY_FAKE_SUCCESS` environment variable.*


(WAKEPY_FAKE_SUCCESS)=
## WAKEPY_FAKE_SUCCESS
To force wakepy to fake a successful mode activation, you may set an environment variable `WAKEPY_FAKE_SUCCESS` to a *truthy value* like `yes` or `1`.  This makes all wakepy Modes to insert a special fake method called `WakepyFakeSuccess` to its list of Methods. This method is always the highest priority (tried first), and it's activation guaranteed to succeed. This works with any mode and on any platform. Since the `WakepyFakeSuccess` Method is tried *before* any other possible Methods,  there will be no IO (except for the env var check), and no calling of any executables or 3rd party services when `WAKEPY_FAKE_SUCCESS` is used.


```{admonition} Truthy and falsy values
:class: info
Only `0`, `no`, `N`, `false`, `F` and the empty string are considered as falsy values (case ignored). Any other value is considered truthy.
```
```{admonition} Distinguishing real activation success from a faked one
:class: tip

If you need to check if the activation was real or a faked one, you can use the {attr}`Mode.activation_result <wakepy.Mode.activation_result>` which is an {class}`ActivationResult <wakepy.ActivationResult>` instance, and check the {attr}`ActivationResult.real_success <wakepy.ActivationResult.real_success>` attribute.
```

### pytest

To set `WAKEPY_FAKE_SUCCESS` in a single test, you may use the [monkeypatch](https://docs.pytest.org/en/latest/how-to/monkeypatch.html) fixture:

```{code-block} python
def test_foo(monkeypatch):
    monkeypatch.setenv("WAKEPY_FAKE_SUCCESS", "yes")
    # ... the test code
```

### tox

If using [tox](https://tox.wiki/), use [`setenv`](https://tox.wiki/en/4.14.2/config.html#set_env) (aka. `set_env`) in your tox.ini:

```{code-block} ini
[testenv]
# ... other settings
setenv =
    WAKEPY_FAKE_SUCCESS = "yes"
```

### nox

If using [nox](https://nox.thea.codes/), set the `WAKEPY_FAKE_SUCCESS` environment variable by adding the key-value pair to `session.env` in your noxfile.py. For example:

```{code-block} python
@nox.session
def tests(session):
    session.env["WAKEPY_FAKE_SUCCESS"] = "yes"
    # ... run tests
```

## Tests without using faked success

If you need to run tests without faking a success, note that on Linux wakepy uses D-Bus methods to inhibit screensaver or power management. Therefore, you need to have `DBUS_SESSION_BUS_ADDRESS` set to the session D-Bus address. This is usually automatically set, but test runners might drop out set environment variables.

To pass the `DBUS_SESSION_BUS_ADDRESS` with tox, one would use [`passenv`](https://tox.wiki/en/4.14.2/config.html#passenv):

```{code-block} ini
[testenv]
# ... other settings
passenv =
    DBUS_SESSION_BUS_ADDRESS
```