"""Test all the different wakepy Methods which may be used to enter or keep a
Mode.

Tests include:
* Test for using all the defined methods; for example, running `enter_mode()`
 and  `exit_mode` using fake/mock adapters (DBusAdapter, etc.), or mocks for
 io related things.

Tests Exclude:
* IO of any kind & calling 3rd party executables
* Usage of DBus services, even fake ones
"""
