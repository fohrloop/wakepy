# API Reference 

```{eval-rst}

.. autosummary::

    wakepy.keep.running
    wakepy.keep.presenting
    wakepy.DbusAdapter

Wakepy Modes
-------------
.. autofunction:: wakepy.keep.running 
.. autofunction:: wakepy.keep.presenting 

DBus Adapter
-------------
Dbus adapters are an advanced concept of wakepy. They would be used in such a case where wants to use other D-Bus python library than the default (which is `jeepney <https://jeepney.readthedocs.io/>`_).

.. autoclass:: wakepy.DbusAdapter
    :members:

.. autoclass:: wakepy.core.DbusMethodCall
    :members:

.. autoclass:: wakepy.core.DbusMethod
    :members:

```  