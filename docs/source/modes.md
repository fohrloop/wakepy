# Wakepy Modes



The available modes are 
| Wakepy mode       | What it does                                        |
| ----------------- | --------------------------------------------------- |
| `keep.running`    | Automatic sleep is prevented                        |
| `keep.presenting` | Automatic sleep, screensaver & screenlock prevented |

## Entering a mode

The wakepy modes are implemented as context managers of type `wakepy.Mode`. When entering the context, the `wakepy.Mode` instance (`m`) is returned, which has following attributes:

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

## wakepy.keep.running


**Does keep.running prevent manually putting system to sleep?** All the methods, if not otherwise specified, only prevent the *automatic, idle timer timeout based* sleeping, so it is still possible to put system to sleep by selecting Suspend/Sleep from a menu, closing the laptop lid or pressing a power key, for example. One exception is systemd mask method on Linux, which prevents suspend altogether.

**Can I lock my computer after entered `keep.running` mode?**: Yes, and you probably should, if you're not near your computer. The programs will continue execution regardless of the lock.



## wakepy.keep.presenting


**Does keep.presenting prevent manually putting system to sleep?** All the methods, if not otherwise specified, only prevent the *automatic, idle timer timeout based*  sleeping and screensaver/screenlock, so it is still possible to put system to sleep by selecting Suspend/Sleep from a menu, closing the laptop lid or pressing a power key, for example. It is also possible to manually start the screenlock/screensaver while presenting mode is on. 

**Is my computer locked automatically in `keep.presenting` mode?**: No. Entering a screenlock automatically would stop presenting the content. 



## General questions
**What if the process holding the lock dies?**: The lock is automatically removed. 

**How to use wakepy in tests / CI**: One problem with tests and/or CI systems is that many times the environment is different, and preventing system going to sleep works differently there. To fake a successful inhibit lock in tests, you may set an environment variable: `WAKEPY_FAKE_SUCCESS` to `yes`.