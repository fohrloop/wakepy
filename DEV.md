# Development

This document serves as documentation for the package developers.

## Branches and tags

- **`dev`** branch: for development. All PRs should be against it. Documented at [wakepy.readthedocs.io/en/dev/](https://wakepy.readthedocs.io/en/dev/)
- **`master`** branch: The stable/released version(s) of wakepy. Documented at [wakepy.readthedocs.io](https://wakepy.readthedocs.io/), which is the same as the [wakepy.readthedocs.io/en/latest/](https://wakepy.readthedocs.io/en/latest/).
- Use a local short-lived feature branch for development.
- Release versions use [Semantic Versioning](https://semver.org/) and are marked with git tags (on the dev branch) with format `v[major].[minor].[patch]`; e.g. v1.2.0 or v2.2.0.

## Installing for development

Requirements:
- At least of of the supported Python versions installed (see README.md and/or tox.ini).
- pip >= 21.3 (for pyproject.toml support)

Install in editable state with the `dev` requirements:
```
python -m pip install -r requirements/requirements-dev.txt -e .
```

where `.` means the current directory (assuming cwd is at root of the repository).

## Documentation

- The documentation is done with Sphinx and the source code lives at
 `./docs/source`.
- **Building locally** (for debugging / testing docs), with autobuild:

```
invoke docs
```

- **Deploying**: Just push to github, and it will be automatically built by readthedocs. The settings can be adjusted [here](https://readthedocs.org/dashboard).
- Versions selected for documentation are selected in the readthedocs UI. Select one version per `major.minor` version (latest of them) from the git tags.
- The `latest` version (default versio) in readthedocs follows the `master` branch automatically.



# Testing

Wakepy uses pytest for testing the source tree with one python version and tox for testing the created wheel with multiple python versions.

## Running tests with single environment

- Requirement: Any one python version within the range of supported versions (see README.md or tox.ini)
- Use pytest to run tests within a single environment:

```
invoke test
```
this will (1) run tests in your current python environment against the intalled version
of wakepy (if editable install, uses the source tree), (2) Check code coverage, (3)
run code formatting checks.


## Running tests with multiple environments

- Requirement:  One or more of the python versions mentioned in the envlist in tox.ini have to be installed and available for tox. Missing python versions are going to be simply skipped. If running on UNIX/macOS,
  you may use [pyenv](https://github.com/pyenv/pyenv) to install multiple versions of python.
- To run the tests with multiple python versions, use tox:

```
tox
```

- To start a debugger on error with a specific python version, select the tox environment with "-e <envname>" and add "-- --pdb" to start the python debugger on error. For example:

```
tox -e py310 -- --pdb
```

- When using tox within this project, what happens is (1) wakepy is built with `python -m build`. This creates sdist from source tree and then wheel from the sdist. (2) Tests are ran against the created *wheel* (if not `skip_install=True` for that environment).

# Deployment

- Create a wheel with

```
python -m pip wheel --no-deps .
```
- Push to PyPI  (assuming the one-time setup below done)
```
python -m twine  upload wakepy-<version>-py3-none-any.whl --repository wakepy
```
- If made a new version, remember to update the `master` branch so ReadTheDocs may update the documentation.
- Also, check that readthedocs has included all the correct versions (git tags)


## Setting up twine/pip for uploading to PyPI
- This should be done once per system
- (1) Get a PyPI token for the *project* from [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
- (2) Create a `$HOME/.pypirc` file with following contents:

```
[distutils]
  index-servers =
    pypi
    wakepy

[pypi]
  username = __token__
  password = # either a user-scoped token or a project-scoped token you want to set as the default

[wakepy]
  repository = https://upload.pypi.org/legacy/
  username = __token__
  password = # the wakepy project scoped token here.
```