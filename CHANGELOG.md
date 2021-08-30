## [0.4.3] (2021-08-28)
### Fixed
- Raising `TypeError: a bytes-like object is required, not 'str'` if trying to use on MacOS (Python 3.9). [Issue 11](https://github.com/np-8/wakepy/issues/11)
## [0.4.2] (2021-08-10)
### Fixed
- Raising `FileNotFoundError` if trying to use on MacOS. Previous implementation had a bug. [Issue 9](https://github.com/np-8/wakepy/issues/9)

## [0.4.1] (2021-06-15)
### Fixed
- Raising `NotImplementedError` if trying to use on Linux without `systemctl`. Previous implementation had a bug. [Issue 8](https://github.com/np-8/wakepy/issues/8)


## [0.4.0] (2021-06-09)
### Added 
- `keepawake` context manager. [[#6](https://github.com/np-8/wakepy/pull/6)]

## [0.3.2] (2021-06-06)
### Fixed
- Raising `NotImplementedError` if trying to use on Linux without `systemctl`. [[#3](https://github.com/np-8/wakepy/pull/3)]

## [0.3.1] (2021-06-02)
### Fixed
- The package in PyPI did not have any content

## [0.3.0] (2021-05-05)
### Added
- Linux & OSX support. Thanks for [rileyyy](https://github.com/rileyyy).