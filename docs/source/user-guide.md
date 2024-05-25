# User Guide

Wakepy main Python API is are the wakepy [Modes](#wakepy-modes), which are states that are activated and deactivated and which keep your system awake. The method for activating the mode depends on your platform (among other things) and is determined by the used [Method](#wakepy-methods).  For example [keep.presenting](#keep-presenting-mode) mode is implemented by [org.gnome.SessionManager](#keep-presenting-org-gnome-sessionmanager) for Linux with GNOME DE, [SetThreadExecutionState](#keep-presenting-windows-stes) for Windows and [caffeinate](#keep-presenting-macos-caffeinate) for MacOS. In most cases, wakepy does nothing but calls an executable (caffeinate), a DLL function call (SetThreadExecutionState) or a D-Bus method (org.gnome.SessionManager). Wakepy helps in this by providing a coherent API which should just work™ on any system. Or, at least that is the vision of wakepy.


## Entering a wakepy.Mode

The wakepy modes are implemented as context managers of type `wakepy.Mode`; either keep.presenting or keep.running:

```{code-block} python
from wakepy import keep

with keep.running():
    # Do something that takes a long time. The system may start screensaver
    # / screenlock or blank the screen, but CPU will keep running.
```

 When entering the context, the `wakepy.Mode` instance (`m`) is returned, which has following attributes:

- `m.active`: True, if entering mode was successful. Can be [faked in CI](./tests-and-ci.md#wakepy_fake_success).
- `m.activation_result`: An ActivationResult instance which gives more detailed information about the activation process.

````{tip}
You may want to inform user about failure in activating a mode. For example:

```{code-block} python
with keep.running() as m:
    if not m.active:
        print('Failed to inhibit system sleep.')

    do_something_that_takes_long_time()
```
````

(on-fail-action)=
## Controlling the on-fail action

By default, if a mode cannot be activated, an {class}`~wakepy.ActivationError` is raised. The {func}`keep.presenting <wakepy.keep.presenting>` and {func}`keep.running <wakepy.keep.running>` also take an `on_fail` parameter which may be used to alter the behavior.

```{versionadded} 0.8.0
```

### on-fail actions

| `on_fail`                | What happens? |
| ------------------------ | ------------ |
| "error"  (default)    | Raises an {class}`~wakepy.ActivationError`        |
| "warn"  | Issues an {class}`~wakepy.ActivationWarning` |
| "pass"  | Does nothing |
| Callable | The callable is called with one argument: the result of the activation which is <br> a instance of {class}`~wakepy.ActivationResult`. The call occurs before the with block is entered. |

#### Example: Notify user with a custom callable

This is what you could do if you want to inform the user that the activation of the mode was not successful, but still want to continue to run the task:

```python
from wakepy import keep, ActivationResult

def react_on_failure(result: ActivationResult):
    print(f'Failed to keep system awake using {result.mode_name} mode')

def run_long_task():
    print('Running a long task')

with keep.running(methods=[], on_fail=react_on_failure):
    print('started')
    run_long_task()
```

- The `on_fail` parameter to {func}`keep.running <wakepy.keep.running>` is a callable which gets called with an {class}`~wakepy.ActivationResult` when the activation of the mode fails.
- Here we use empty list in `methods` to force failure

Example output:

```
Failed to keep system awake using keep.running mode
started
Running a long task
```

#### Example: Notify user and exit

This is what you could do if you want to inform the user that the activation of the mode was not successful, and then exit from the with block:

```python
from wakepy import keep, ActivationResult, ModeExit

def react_on_failure(result: ActivationResult):
    print(f'Failed to keep system awake using {result.mode_name} mode')

def run_long_task():
    print('Running a long task')

with keep.running(methods=[], on_fail=react_on_failure) as m:
    print('started')

    if not m.active:
        print('exiting')
        raise ModeExit

    run_long_task()
```

- The difference to the previous example is the {class}`ModeExit <wakepy.ModeExit>` which is used to exit the with block, if the {attr}`Mode.active <wakepy.Mode.active>` is not `True`.


Example output (notice that `run_long_task` was never called):

```
Failed to keep system awake using keep.running mode
started
exiting
```


(which-method-was-used))=
## Which wakepy Method was used?

When you would like to check *how* exactly did wakepy do what you asked it to,
you can check the used method from the {class}`Mode <wakepy.Mode>` instance.

**Example**

```python
from wakepy import keep

with keep.running() as m:
    print('active_method:', m.active_method)
    print('used_method:', m.used_method)

print('--------')
print('active_method:', m.active_method)
print('used_method:', m.used_method)
```

