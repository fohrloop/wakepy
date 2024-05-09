# Tutorial

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