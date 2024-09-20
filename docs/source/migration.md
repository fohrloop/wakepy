# Migration Guide
## Migration Guide: 0.10.0

### on_fail action

As the previous default `on_fail` value of {func}`keep.running <wakepy.keep.running>` and {func}`keep.presenting <wakepy.keep.presenting>` was "error" (=raise Exception if activation fails) and the new default is "warn", *if you still wish to raise Exceptions*, use the following:

  
```{code-block} python
from wakepy import keep

with keep.running(on_fail="error"):
  do_something()
```


## Migration Guide: 0.8.0

### Decision when keepawake fails

The old way (wakepy <= 0.8.0) was:

```{code-block} python
from wakepy import keep

with keep.running() as m:
  if not m.success:
    # optional: signal to user?
  do_something()
```

On wakepy 0.8.0 one should use the `on_fail` parameter for controlling what to do if activation fails. See the [Controlling the on_fail action](#on-fail-action) in the [User Guide](#user-guide).  A minimum example would be:


```{code-block} python
from wakepy import keep

with keep.running(on_fail=react_on_failure) as m:   
    do_something()

def react_on_failure(result: ActivationResult):
    print(f'Failed to keep system awake using {result.mode_name} mode')
```

See the {class}`ActivationResult <wakepy.ActivationResult>` docs for more details on what's available on the `result` object. The `m.success` does not exist anymore, as the type of `m` is now an instance of {class}`Mode <wakepy.Mode>`. It has {attr}`Mode.active <wakepy.Mode.active>`. and {attr}`Mode.activation_result <wakepy.Mode.activation_result>`. as well as {attr}`Mode.active_method <wakepy.Mode.active_method>` and  {attr}`Mode.used_method <wakepy.Mode.used_method>`.

## Migration Guide: 0.7.0

- When migrating from wakepy <=0.6.0 to 0.7.0
-  `set_keepawake` and `unset_keepawake` and `keepawake`: Replace with `keep.running` or `keep.presenting`, whichever makes sense in the application.

### Python API
#### wakepy <=0.6.0
```{code-block} python
from wakepy import keepawake

with keepawake():
  do_something()
```

or

```{code-block} python
from wakepy import set_keepawake, unset_keepawake

set_keepawake()
do_something()
unset_keepawake()
```

#### wakepy 0.7.0
```{code-block} python
from wakepy import keep

with keep.running() as m:
  if not m.success:
    # optional: signal to user?
  do_something()
```

or

```{code-block} python
from wakepy import keep

with keep.presenting() as m:
  if not m.success:
    # optional: signal to user?
  do_something()
```

### CLI

- Replace `-s` / `--keep-screen-awake` with `-p` / `--presentation`;

### wakepy <= 0.6.0
```
wakepy -s
```
### wakepy 0.7.0
```
wakepy -p
```
