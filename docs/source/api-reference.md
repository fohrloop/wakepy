<!-- NOTE: If you change the title (API Reference), you must update the code
in wakepy-docs.js! -->
# API Reference
```{eval-rst}

.. autosummary::

    wakepy.keep.running
    wakepy.keep.presenting
    wakepy.DBusAdapter

Wakepy Modes
-------------
.. autofunction:: wakepy.keep.running
.. autofunction:: wakepy.keep.presenting

Wakepy Core
------------
.. autoclass:: wakepy.Mode
    :members:

    .. automethod:: __enter__

    .. automethod:: __exit__

.. autoclass:: wakepy.Method
    :members:

.. autoclass:: wakepy.ActivationResult
    :members:

.. autoclass:: wakepy.ActivationError
    :exclude-members: args, with_traceback


DBus Adapter
-------------
DBus adapters are an advanced concept of wakepy. They would be used in such a case where wants to use other D-Bus python library than the default (which is `jeepney <https://jeepney.readthedocs.io/>`_).

.. autoclass:: wakepy.DBusAdapter
    :members:

.. autoclass:: wakepy.core.DBusMethodCall
    :members:

.. autoclass:: wakepy.core.DBusMethod
    :members:
    :exclude-members: count, index

.. autoclass:: wakepy.dbus_adapters.jeepney.JeepneyDBusAdapter
    :members:

```