# Migration Guide
## Migration Guide: 0.7.0

- When migrating from wakepy <=0.6.0 to >=0.7.0
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

#### wakepy >=0.7.0
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
### wakepy >= 0.7.0
```
wakepy -p
```
