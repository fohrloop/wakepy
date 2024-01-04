"""Test all the different wakepy Methods which may be used to enter or keep a
Mode.

Tests include:
* Test for using all the defined methods; for example, running `enter_mode()`
 and  `exit_mode` using fake/mock adapters (DBusAdapter, etc.)

Tests Exclude:
* IO when processing Calls
* Usage of Dbus services, even fake ones
"""
