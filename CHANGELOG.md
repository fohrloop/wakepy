# Changelog

## wakepy 0.8.0
🗓️ not published

### ✨ Features
- Modes support [on-fail actions](#on-fail-action) ("error", "warn", "pass" or a callable).
- It is now possible to select the used wakepy.Methods with `methods` and  `omit` and to change the priority order of methods with `methods_priority`.

### 🚨 Backwards incompatible
- Removed `set_keepawake` and `unset_keepawake functions` and the `keepawake` context manager. These were deprecated in 0.7.0 and are replaced with the new api: `keep.running` and `keep.presenting` context managers.
- If Mode activation fails, raise `wakepy.ActivationError` by default. Previously there was no "on fail" action, but users needed to check the `result.success` to make sure the activation was successful.
- The `WAKEPY_FAKE_SUCCESS` check is done *before* any other Methods (previously, it would be checked if all other methods failed)


## wakepy 0.7.2
🗓️ 2023-09-27

### 🐞 Bug fixes
- The CLI API on python 3.7 and python 3.8. Thanks to [Aymane11](https://github.com/Aymane11) for [PR #50](https://github.com/fohrloop/wakepy/pull/50)

## wakepy 0.7.1 
🗓️ 2023-06-11

### 🐞 Bug fixes
- `keep.running` and `keep.presenting` return an object `m` with `success` value of `True`.

## wakepy 0.7.0
🗓️ 2023-06-11

### ✨ Features
- New API: `keep.running()` and `keep.presenting()` context managers. These are currently simple wrappers of the old methods but the internals will be re-written in a future version.
- The context managers now return the result of the action, `m`. Users may check with `m.success` if changing the mode was successful.
- Possibility to fake successful change of mode with `WAKEPY_FAKE_SUCCESS` (for CI / tests).
### 🐞 Bug fixes
- No exceptions anymore on import-time. All exceptions should be handled now gracefully, and user is informed if switching to a `keep.running` or `keep.presenting` mode failed.

### ⚠️ Deprecations
- Old Python API:  The `keepawake()`, `set_keepawake` and `unset_keepwake`. These will be removed in a future version of wakepy. Use `keep.running()`or `keep.presenting()`, instead.
- The `-s, --keep-screen-awake` option of the `wakepy` CLI command. Use `-p, --presentation ` option, instead.

## wakepy 0.6.0
🗓️ 2023-02-27

### ✨ Features
- Support for using wakepy without sudo on linux! There are now D-bus solutions (1) using  jeepney and (2) using dbus-python (libdbus). Thanks to [Stehlampe2020](https://github.com/Stehlampe2020) for the dbus-python based solution ([PR #22](https://github.com/np-8/wakepy/pull/22)) and [NicoWeio](https://github.com/NicoWeio) for raising  [Issue #17](https://github.com/np-8/wakepy/issues/17).
- Linux+systemd approach has sudo check. The program won't start without `SUDO_UID` environment variable set.

## wakepy 0.5.0
🗓️ 2021-12-15

### ✨ Features
- wakepy ascii art text, version and options will be printed in console if wakepy launched with the CLI
- The `wakepy` executable for CLI is installed when `wakepy` is installed with `pip`.

## wakepy 0.4.4
🗓️ 2021-08-30

### 🐞 Bug fixes
- Keeping screen awake on Mac ([#13](https://github.com/np-8/wakepy/issues/13)). Fixed in [PR #15](https://github.com/np-8/wakepy/pull/15). Thanks to [mikeckennedy](https://github.com/mikeckennedy).

## wakepy 0.4.3
🗓️ 2021-08-28

### 🐞 Bug fixes
- Raising `TypeError: a bytes-like object is required, not 'str'` if trying to use on MacOS (Python 3.9) ([#11](https://github.com/np-8/wakepy/issues/11)). Thanks to [mikeckennedy](https://github.com/mikeckennedy) for [PR #12](https://github.com/np-8/wakepy/pull/12).

## wakepy 0.4.2
🗓️ 2021-08-10

### 🐞 Bug fixes
- Raising `FileNotFoundError` if trying to use on MacOS. Previous implementation had a bug ([#9](https://github.com/np-8/wakepy/issues/9)). Thanks to [matacoder](https://github.com/matacoder) for [PR #10](https://github.com/np-8/wakepy/pull/10).

## wakepy 0.4.1
🗓️ 2021-06-15

### 🐞 Bug fixes
- Raising `NotImplementedError` if trying to use on Linux without `systemctl`. Previous implementation had a bug. ([#8](https://github.com/np-8/wakepy/issues/8))


## wakepy 0.4.0
🗓️ 2021-06-09

### ✨ Features
- `keepawake` context manager. ([#6](https://github.com/np-8/wakepy/pull/6)). Thanks to [HoustonFortney](https://github.com/HoustonFortney).

## wakepy 0.3.2
🗓️ 2021-06-06

### 🐞 Bug fixes
- Raising `NotImplementedError` if trying to use on Linux without `systemctl`. ([#3](https://github.com/np-8/wakepy/pull/3))

## wakepy 0.3.1
🗓️ 2021-06-02

### 🐞 Bug fixes
- The package in PyPI did not have any content

## wakepy 0.3.0
🗓️ 2021-05-05

### ✨ Features
- Linux & OSX support. Thanks for [rileyyy](https://github.com/rileyyy).