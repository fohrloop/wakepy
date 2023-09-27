# Development

This document serves as documentation for the package developers.

## Branches

- wakepy uses the `main` branch for development. All PRs should be against it. This is the only long-lived branch in the repo.
- Use a local short-lived feature branch for development.
- Release versions are use [Semantic Versioning](https://semver.org/) and are marked with git tags (on the main branch) with format `v[major].[minor].[patch]`; e.g. v1.2.0 or v2.2.0.



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

- Versions selected for documentation are selected in the readthedocs UI. Select one version per `major.minor` version (latest of them) from the git tags. 
  



# Testing 

- wakepy uses pytest
- To run tests with coverage, use

```
coverage run -m pytest <test-target> coverage html && python -m webbrowser -t htmlcov/index.html 
```


# Deployment

- Create a wheel with

```
python -m pip wheel --no-deps .
```
- Push to PyPI 
  - Once per system: (1) get a PyPI token for the *project* from [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/) 

```
twine upload wakepy-<version>-py3-none-any.whl 
```