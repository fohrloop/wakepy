# User Guide


## Wakepy in tests and CI

If you're using wakepy in Continuous Integration tests, note that typically CI is running on a system where there is no Desktop Environment available. In addition, the available services and executables might be different from the services and executables you have on your machine. For this reason, even if wakepy is able to switch to a mode on your machine, it might not be able to do so in CI tests.

### WAKEPY_FAKE_SUCCESS
To force wakepy to fake a succesful mode switch, you may set an environment variable `WAKEPY_FAKE_SUCCESS` to `yes`. This makes wakepy to fake the succesful mode change after all other methods have failed.

In tox, this would be:

```ini
[testenv]
# ... other settings
setenv = 
    WAKEPY_FAKE_SUCCESS = "yes"
```

### DBUS_SESSION_BUS_ADDRESS

On Linux, wakepy uses D-Bus methods to inhibit screensaver or power management. Therefore, you need to have `DBUS_SESSION_BUS_ADDRESS` set to the session D-Bus address. This is usually automatically set, but test runners might drop out set environment variables. 

To pass the `DBUS_SESSION_BUS_ADDRESS` with tox, one would use:

```ini
[testenv]
# ... other settings
passenv = 
    DBUS_SESSION_BUS_ADDRESS
```