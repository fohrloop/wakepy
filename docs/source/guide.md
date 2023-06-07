# User Guide


## Wakepy in CI tests

If you're using wakepy in Continuous Integration tests, note that typically CI is running on a system where there is no Desktop Environment available. In addition, the available services and executables might be different from the services and executables you have on your machine. For this reason, even if wakepy is able to switch to a mode on your machine, it might not be able to do so in CI tests.

### WAKEPY_FAKE_SUCCESS
To force wakepy to fake a succesful mode switch, you may set an environment variable `WAKEPY_FAKE_SUCCESS` to `"yes"`. This makes wakepy to fake the succesful mode change after all other methods have failed.