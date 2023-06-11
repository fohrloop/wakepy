# Development

This document serves as documentation for the package developers.

## Installing for development

Install in editable state with the `doc` and `dev` options:
```
python -m pip install -e .[doc,dev]
```

where `.` means the current directory (assuming cwd is at root of the repository).
## Documentation

- The documentation is done with Sphinx and the source code lives at 
 `./docs/source`.
- **Building locally** (for debugging / testing docs), with autobuild:

```
sphinx-autobuild docs/source/ docs/build/ -a
```

The `-a` flag ensures that *all* files (not only edited files) will get rebuild. It is also possible to build just one time:
```
sphinx-build -b html docs/source/ docs/build
```
- **Deploying**: Just push to github, and it will be automatically built by readthedocs. The settings can be adjusted [here](https://readthedocs.org/dashboard).