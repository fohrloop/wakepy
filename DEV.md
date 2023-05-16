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
- **Building locally** (for debugging / testing docs): 

```
sphinx-build -b html docs/source/ docs/built
```
- **Deploying**: Just push to github, and it will be automatically built by readthedocs. The settings can be adjusted [here](https://readthedocs.org/dashboard).