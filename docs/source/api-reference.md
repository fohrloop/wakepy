<!-- NOTE: If you change the title (API Reference), you must update the code
in wakepy-docs.js! -->
# API Reference

```{admonition} Wakepy API is still experimental 🚧
:class: note

Since wakepy is still 0.x.x, the API might change without further notice from
one release to another. After that, breaking changes should occur only part of
a major release (e.g. 1.x.x -> 2.0.0). 
```


```{eval-rst}

.. autosummary::

    wakepy.keep.running
    wakepy.keep.presenting

Wakepy Modes
-------------
.. autofunction:: wakepy.keep.running
.. autofunction:: wakepy.keep.presenting

Wakepy Core
------------
.. autoclass:: wakepy.Mode
    :members: name,
              activation_result,
              active_method,
              used_method,
              active,
              methods_priority,
              on_fail,
    :member-order: bysource

.. autoclass:: wakepy.MethodInfo
    :members:

.. autoclass:: wakepy.ActivationResult
    :members:
    :exclude-members: results
    :member-order: bysource

.. autoclass:: wakepy.MethodActivationResult
    :members: method,
              success,
              method_name,
              mode_name,
              failure_stage,
              failure_reason,
    :member-order: bysource

.. autoclass:: wakepy.ActivationError
    :exclude-members: args, with_traceback

.. autoclass:: wakepy.ActivationWarning
    :exclude-members: args, with_traceback

.. autoclass:: wakepy.ModeExit
    :exclude-members: args, with_traceback

.. autoclass:: wakepy.core.constants.PlatformType
  :members:
  :undoc-members:
  :member-order: bysource

.. autoclass:: wakepy.core.constants.IdentifiedPlatformType
  :members:
  :undoc-members:
  :member-order: bysource

.. autodata:: wakepy.core.platform.CURRENT_PLATFORM
  :no-value:

.. autoclass:: wakepy.ModeName
  :members:
  :undoc-members:
  :member-order: bysource

.. autoclass:: wakepy.Method
    :members:

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

.. autoclass:: wakepy.JeepneyDBusAdapter
    :members:

```