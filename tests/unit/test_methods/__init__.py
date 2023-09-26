"""Test all the different wakepy Methods which may be used to enter or keep a
Mode.

Tests include:
* Test for using all the defined methods; for example, running `enter_mode()`
 and  `exit_mode` using mocks in place of 3rd party software

Tests Exclude:
* Calling io; No calling any executables or dbus methods (3rd party sw). First,
  3rd party sw is assumed to be tested in their respective repos and their
  functionality will not be tested in the automated tests of wakepy. Although,
  known bugs in specific versions of 3rd party sw will be acted upon in wakepy,
  when possible. Second, calling io in wakepy is done through Adapters, and the
  adapters are tested separately.
* Testing that the 3rd party sw calls are actually written correctly (as we
  don't call 3rd party sw). This means that the names defining the SW, i.e. the
  MyMethod(Method) subclass with its attributes, must be tested *manually*
  once (and only once).
"""
