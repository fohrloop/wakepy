# Changelog

## wakepy 0.9.0.post1
🗓️ 2024-06-01

### 📖 Documentation
- Update docs and README after 0.8.0 & 0.9.0 releases ([#331](https://github.com/fohrloop/wakepy/pull/331))


## wakepy 0.9.0
🗓️ 2024-05-31

### ✨ Features
- Support keep.running mode in KDE Plasma 5.12.90 and newer through the [org.freedesktop.PowerManagement](#org-freedesktop-powermanagement) method. It may also be used on other DEs which implement this older freedesktop.org D-Bus interface (but not Xcfe). ([#324](https://github.com/fohrloop/wakepy/pull/324))
- Cooler CLI spinner ([#309](https://github.com/fohrloop/wakepy/pull/309), [#323](https://github.com/fohrloop/wakepy/pull/323))

### 📖 Documentation
- Document that the [org.freedesktop.ScreenSaver](org-freedesktop-screensaver) method for keep.presenting mode also supports KDE Plasma. ([#324](https://github.com/fohrloop/wakepy/pull/324))
- Update dev docs ([#308](https://github.com/fohrloop/wakepy/pull/308))
- Mention that shell should be restarted for wakepy CLI tool ([#321](https://github.com/fohrloop/wakepy/pull/321))
- Fix: Supported Platforms table background does not support dark mode ([#316](https://github.com/fohrloop/wakepy/pull/316))

## wakepy 0.8.0
🗓️ 2024-05-26

### 🏆 Highlights
- This is a basically a complete rewrite of wakepy. It adds support for keep.running mode on Gnome, on-fail action, possibility to control the used methods and their priority, more information about the used methods and the activation process and possibility to exit the mode early. In addition, testing and CI pipelines were updated to ease maintenance.

### ✨ Features
- Modes support [on-fail actions](#on-fail-action) ("error", "warn", "pass" or a callable). ([#182](https://github.com/fohrloop/wakepy/pull/182))
- It is now possible to [select the used wakepy.Methods](#how-to-white-or-blacklist-methods) with `methods` and  `omit` and to [change the priority order](#how-to-control-order-of-methods) of methods with `methods_priority`. ([#75](https://github.com/fohrloop/wakepy/issues/75))
- Added [org.gnome.SessionManager](#org-gnome-sessionmanager) method which adds support for keep.running mode for users with Gnome Desktop Environment. ([#51](https://github.com/fohrloop/wakepy/pull/51), [#138](https://github.com/fohrloop/wakepy/pull/138), [#278](https://github.com/fohrloop/wakepy/pull/278), [#282](https://github.com/fohrloop/wakepy/pull/282))
- {class}`ActivationResult <wakepy.ActivationResult>` objects ([#57](https://github.com/fohrloop/wakepy/pull/57), [#258](https://github.com/fohrloop/wakepy/pull/258), [#270](https://github.com/fohrloop/wakepy/pull/270)) in {attr}`Mode.activation_result <wakepy.Mode.activation_result>` which give more detailed information about the activation process.
- Possibility to exit from a mode context manager early with {class}`ModeExit <wakepy.ModeExit>`  ([#72](https://github.com/fohrloop/wakepy/pull/72))
- It's now possible to check the active and used method from the Mode instance using the {attr}`Mode.active_method <wakepy.Mode.active_method>` and  {attr}`Mode.used_method <wakepy.Mode.used_method>` ([#268](https://github.com/fohrloop/wakepy/pull/268))
- Added possibility to use any dbus python implementation through the {class}`DBusAdapter <wakepy.DBusAdapter>`. By default uses jeepney through {class}`JeepneyDBusAdapter <wakepy.JeepneyDBusAdapter>`  (See: [#45](https://github.com/fohrloop/wakepy/issues/45))
### 🚨 Backwards incompatible
- Removed `set_keepawake` and `unset_keepawake functions` and the `keepawake` context manager. These were deprecated in 0.7.0 and are replaced with the new api: {func}`keep.running() <wakepy.keep.running>` and {func}`keep.presenting() <wakepy.keep.presenting>` context managers. ([#85](https://github.com/fohrloop/wakepy/pull/85))
- Renamed the CLI argument `-s, --keep-screen-awake` to `-p, --presentation`. The old ones were deprecated in 0.7.0. ([#179](https://github.com/fohrloop/wakepy/pull/179/))
- If Mode activation fails, raise {class}`ActivationError <wakepy.ActivationError>` by default. Previously there was no "on fail" action, but users needed to check the `result.success` to make sure the activation was successful.
- The org.freedesktop.ScreenSaver based method is not used on keep.running mode. Systems supporting org.freedesktop.ScreenSaver which are not running Gnome will have no keep.running method until it gets implemented. By default wakepy will raise a wakepy.ActivationError if keep.running is used on such system. Either use keep.preseting mode, or wait or provide a PR.
- The [WAKEPY_FAKE_SUCCESS](#WAKEPY_FAKE_SUCCESS) check is done *before* trying any wakepy Methods (previously, it was used when all the tried methods have failed)

### 🐞 Bug fixes
- The org.freedesktop.ScreenSaver based method is only used in keep.presenting mode. Previously, it was used on keep.running mode on Linux. ([#46](https://github.com/fohrloop/wakepy/issues/46), [#136](https://github.com/fohrloop/wakepy/issues/136))
- Still going to sleep - running Fedora 36 ([#18](https://github.com/fohrloop/wakepy/issues/18))

### 📖 Documentation
- Rewritten the docs ([#193](https://github.com/fohrloop/wakepy/pull/193), [#194](https://github.com/fohrloop/wakepy/pull/194), [#196](https://github.com/fohrloop/wakepy/pull/196), [#197](https://github.com/fohrloop/wakepy/pull/197), [#198](https://github.com/fohrloop/wakepy/pull/198), [#200](https://github.com/fohrloop/wakepy/pull/200), [#244](https://github.com/fohrloop/wakepy/pull/244), [#271](https://github.com/fohrloop/wakepy/pull/271), [#272](https://github.com/fohrloop/wakepy/pull/272), [#285](https://github.com/fohrloop/wakepy/pull/285), [#286](https://github.com/fohrloop/wakepy/pull/286))
- Remove /en/ from the URL and rename latest to stable ([#250](https://github.com/fohrloop/wakepy/pull/250))

### 👷 Maintenance
- Made the CI tests mandatory for every PR (previously manual) ([#191](https://github.com/fohrloop/wakepy/pull/191))
- 100% test coverage + use branch coverage instead of line coverage + enforce 100% coverage ([#221](https://github.com/fohrloop/wakepy/pull/221), [#222](https://github.com/fohrloop/wakepy/pull/222))
- Run black+isort+ruff also on tests ([#224](https://github.com/fohrloop/wakepy/pull/224))
- Run mypy also on tests + fix the new mypy issues ([#227](https://github.com/fohrloop/wakepy/pull/227))
- Add tests for Python 3.12 and 3.13. Now test all supported versions of python on linux, and oldest and newest supported versions on MacOS and Windows.  ([#160](https://github.com/fohrloop/wakepy/pull/160), [#236](https://github.com/fohrloop/wakepy/pull/236), [#273](https://github.com/fohrloop/wakepy/pull/273))
- Pin docs and tests dependencies ([#220](https://github.com/fohrloop/wakepy/pull/220))
- Build docs in CI tests to prevent breaking docs ([#211](https://github.com/fohrloop/wakepy/pull/211))
- Run tox and pipeline tests against build wheel instead of the source tree ([#231](https://github.com/fohrloop/wakepy/pull/231), [#236](https://github.com/fohrloop/wakepy/pull/236))
- Build both, sdist (tar.gz) and wheel (.whl). 0.7.x had just wheels and <=0.6.x just dist. Start using setuptools-scm and switch from flit to setuptools ([#235](https://github.com/fohrloop/wakepy/pull/235)).
- Add invoke commands ([#223](https://github.com/fohrloop/wakepy/pull/223))
- Add automatic publishing GitHub workflow ([#238](https://github.com/fohrloop/wakepy/pull/238))
- Limit docstrings and comments to 79 characters ([#207](https://github.com/fohrloop/wakepy/pull/207))
- WakepyFakeSuccess Method ([#152](https://github.com/fohrloop/wakepy/pull/152)) instead of using some custom logic with `WAKEPY_FAKE_SUCCESS`.
- Split package extras: dev, doc, test and check (was: doc, dev) ([#213](https://github.com/fohrloop/wakepy/pull/213)) and start using requirements-*.txt instead of misusing extras ([#228](https://github.com/fohrloop/wakepy/pull/228))
- Ruff: Update from 0.0.270 to 0.3.2 ([#206](https://github.com/fohrloop/wakepy/pull/206)), use `--no-fix` in tox ([#208](https://github.com/fohrloop/wakepy/pull/208)), Stricter ruff rules: W291 ([#209](https://github.com/fohrloop/wakepy/pull/209))
- Black: Update from 23.3.0 to 24.2.0 and reformat ([#217](https://github.com/fohrloop/wakepy/pull/217))
- Isort: Update from 5.12.0 to 5.13.2 ([#218](https://github.com/fohrloop/wakepy/pull/218))
- Mypy: Update from 1.3.0 to 1.9.0 ([#219](https://github.com/fohrloop/wakepy/pull/219)), stricter settings; `disallow_untyped_defs = true` ([#242](https://github.com/fohrloop/wakepy/pull/242)), `disallow_any_unimported = true` and `warn_unused_ignores = true` ([#243](https://github.com/fohrloop/wakepy/pull/243))
- Make wakepy statically typed: Add py.typed ([PEP 561](https://peps.python.org/pep-0561/)) to advertize that wakepy is a fully typed package ([#232](https://github.com/fohrloop/wakepy/pull/232)), add mypy checks on 3.7-3.12 ([#265](https://github.com/fohrloop/wakepy/pull/265))
- Other tox improvements ([#233](https://github.com/fohrloop/wakepy/pull/233))
- Convert from flat layout to src layout ([#234](https://github.com/fohrloop/wakepy/pull/234))
- Cleanup .gitignore ([#237](https://github.com/fohrloop/wakepy/pull/237))

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

### 📖 Documentation
- Created Readthedocs pages

### 👷 Maintenance
* Added manual CI tests
- Start using tox
- Enforce pass in isort, black, ruff and mypy in tests

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