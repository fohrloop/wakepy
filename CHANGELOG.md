# Changelog 

## [0.7.0] (2023-06-11)
### Added
- New API: `keep.running()` and `keep.presenting()` context managers. These are currently simple wrappers of the old methods but the internals will be re-written in a future version. 
- The context managers now return the result of the action, `m`. Users may check with `m.success` if changing the mode was succesful.
- Possibility to fake succesful change of mode with `WAKEPY_FAKE_SUCCESS` (for CI / tests).
### Fixed
- No exceptions anymore on import-time. All exceptions should be handled now gracefully, and user is informed if switching to a `keep.running` or `keep.presenting` mode failed.
  
### Deprecated
- Old Python API:  The `keepawake()`, `set_keepawake` and `unset_keepwake`. These will be removed in a future version of wakepy. Use `keep.running()`or `keep.presenting()`, instead.
- The `-s, --keep-screen-awake` option of the `wakepy` CLI command. Use `-p, --presentation ` option, instead. 

## [0.6.0] (2023-02-27)
### Added
- Support for using wakepy without sudo on linux! There are now D-bus solutions (1) using  jeepney and (2) using dbus-python (libdbus). Thanks to [Stehlampe2020](https://github.com/Stehlampe2020) for the dbus-python based solution ([PR #22](https://github.com/np-8/wakepy/pull/22)) and [NicoWeio](https://github.com/NicoWeio) for raising  [Issue #17](https://github.com/np-8/wakepy/issues/17). 
### Changed
- Linux+systemd approach has sudo check. The program won't start without `SUDO_UID` environment variable set.

## [0.5.0] (2021-12-15)
### Added
- wakepy ascii art text, version and options will be printed in console if wakepy launched with the CLI
- The `wakepy` executable for CLI is installed when `wakepy` is installed with `pip`.

## [0.4.4] (2021-08-30)
### Fixed
- Keeping screen awake on Mac [Issue #13](https://github.com/np-8/wakepy/issues/13) (fixed in [PR #15](https://github.com/np-8/wakepy/pull/15)). Thanks to [mikeckennedy](https://github.com/mikeckennedy).

## [0.4.3] (2021-08-28)
### Fixed
- Raising `TypeError: a bytes-like object is required, not 'str'` if trying to use on MacOS (Python 3.9). [Issue #11](https://github.com/np-8/wakepy/issues/11) Thanks to [mikeckennedy](https://github.com/mikeckennedy) for [PR #12](https://github.com/np-8/wakepy/pull/12).

## [0.4.2] (2021-08-10)
### Fixed
- Raising `FileNotFoundError` if trying to use on MacOS. Previous implementation had a bug. [Issue #9](https://github.com/np-8/wakepy/issues/9). Thanks to [matacoder](https://github.com/matacoder) for [PR #10](https://github.com/np-8/wakepy/pull/10).

## [0.4.1] (2021-06-15)
### Fixed
- Raising `NotImplementedError` if trying to use on Linux without `systemctl`. Previous implementation had a bug. [Issue 8](https://github.com/np-8/wakepy/issues/8)


## [0.4.0] (2021-06-09)
### Added 
- `keepawake` context manager. [[PR #6](https://github.com/np-8/wakepy/pull/6)]. Thanks to [HoustonFortney](https://github.com/HoustonFortney).

## [0.3.2] (2021-06-06)
### Fixed
- Raising `NotImplementedError` if trying to use on Linux without `systemctl`. [[#3](https://github.com/np-8/wakepy/pull/3)]

## [0.3.1] (2021-06-02)
### Fixed
- The package in PyPI did not have any content

## [0.3.0] (2021-05-05)
### Added
- Linux & OSX support. Thanks for [rileyyy](https://github.com/rileyyy).