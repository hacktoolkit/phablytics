[![](https://img.shields.io/pypi/pyversions/phablytics.svg?longCache=True)](https://pypi.org/project/phablytics/)
[![](https://img.shields.io/pypi/v/phablytics.svg?maxAge=3600)](https://pypi.org/project/phablytics/)

# phablytics
Analytics, metrics, and reports for Phabricator (https://phacility.com/phabricator/).

# Get Started

1. `/path/to/pip install phablytics` in your local project.
    1. Or, if installing the web server: `/path/to/pip install phablytics[web]`
1. On your first install on a new machine, you'll want to update interfaces:
    ```
    from phabricator import Phabricator
    phab = Phabricator()
    phab.update_interfaces()
    phab.user.whoami()
    ```
1. Create a `settings.py` file based off of `settings.py`
1. Run the Phablytics CLI and see help: `/path/to/phablytics -h`

# Releasing

1. Update both `VERSION` as well as `__version__` in `phablytics/__init__.py`
1. Update the `CHANGELOG.md` with the details of this release
1. Regenerate a new package for distribution: `make repackage`
1. Upload to PyPI: `make upload`

# Authors and Maintainers

- [Hacktoolkit](https://github.com/hacktoolkit)
- [Jonathan Tsai](https://github.com/jontsai)

# License

MIT. See `LICENSE.md`
