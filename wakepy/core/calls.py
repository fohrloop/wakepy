from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing import Any, List, Optional, Tuple, Type

    from .dbus import DbusAdapter, DbusAdapterTypeSeq, DbusMethod


class Call:
    """Base Call class. Needed at least for type checking and for making
    talking about how everything works easier

    Modes use Methods which create Calls, which are then invoked by an Adapter.
    For example, DbusMethodCalls are invoked by DbusAdapters.
    """


class DbusMethodCall(Call):
    """Represents a Dbus method call with its arguments. Has basic validation
    for the number of arguments (compare args agains the DbusMethod.params, if
    the DbusMethod.params are defined).

    Note: Does not check for validity of args against the input parameter
    signature. This is done only by the underlying Dbus library when doing the
    dbus method calls.
    """

    method: DbusMethod
    """The method which is the target of the call. Must be completely defined.
    """

    args: Tuple[Any, ...]
    """The method args (positional). This is used"""

    def __init__(
        self, method: DbusMethod, args: dict[str, Any] | Tuple[Any, ...] | List[Any]
    ):
        """Converts the `args` argument is converted into a tuple and makes it
        available at DbusMethodCall.args."""
        if not method.completely_defined():
            raise ValueError(
                f"{self.__class__.__name__} requires completely defined DBusMethod!"
            )
        self.method = method
        self.args = self._args_as_tuple(args, method)

    def get_kwargs(self) -> dict[str, Any] | None:
        """Get a keyword-argument representation (dict) of the self.args. If
        the DbusMethod (self.method) does not have params defined, returns
        None."""
        if self.method.params is None:
            return None
        assert isinstance(self.method.params, tuple)

        return {p: arg for p, arg in zip(self.method.params, self.args)}

    def _args_as_tuple(
        self, args: dict[str, Any] | Tuple[Any, ...] | List[Any], method: DbusMethod
    ) -> Tuple[Any, ...]:
        if isinstance(args, tuple) or isinstance(args, list):
            args = tuple(args)
            self.__check_tuple_args(args, method)
            return args

        assert isinstance(args, dict), "args may only be tuple, list or dict"
        return self.__dict_args_as_tuple(args, method)

    def __check_tuple_args(self, args: Tuple[Any, ...], method: DbusMethod) -> None:
        if method.params is None:
            return

        self.__check_args_length(args, method)

    def __check_args_length(self, args: Tuple[Any, ...], method: DbusMethod):
        if len(method.params) != len(args):
            raise ValueError(
                f"Expected args to have {len(method.params)} items! (has: {len(args)})"
            )

    def __dict_args_as_tuple(
        self, args: dict[str, Any], method: DbusMethod
    ) -> Tuple[Any, ...]:
        if not isinstance(method.params, tuple):
            raise ValueError(
                "args cannot be a dictionary if method does not have the params "
                f"defined! Either add params to the DbusMethod '{method.name}' or give "
                "args as a tuple or a list."
            )

        self.__check_args_length(tuple(args), method)

        if set(method.params) != set(args):
            raise ValueError(
                "The keys in `args` do not match the keys in the DbusMethod params!"
                f" Expected: {method.params}. Got: {tuple(args)}"
            )
        return tuple(args[p] for p in method.params)


class CallProcessor:
    """A call processor. Determines *how* to process a call object and
    processes it."""

    def __init__(
        self, dbus_adapter: Optional[Type[DbusAdapter] | DbusAdapterTypeSeq] = None
    ):
        """
        dbus_adapter:
            Determines, which Dbus library / implementation is to be used, if
            Dbus-based methods are to be used with a mode. You may use this to
            use a custom DBus implementation.
        """
        self.dbus_adapter = get_dbus_adapter(dbus_adapter)

    def process(self, call: Call):
        if isinstance(call, DbusMethodCall) and self.dbus_adapter:
            return self.dbus_adapter.process(call)

        else:
            raise NotImplementedError(f"Cannot process a call of type: {type(call)}")


def get_dbus_adapter(
    dbus_adapter: Optional[Type[DbusAdapter] | DbusAdapterTypeSeq] = None,
) -> DbusAdapter | None:
    """Creates a dbus adapter instance"""

    if dbus_adapter is None:
        return get_default_dbus_adapter()

    if isinstance(dbus_adapter, type):
        return dbus_adapter()

    # TODO: create some better logic which tests if the dbus adapter may be
    # used. For now, just return first from the iterable which won't crash upon
    # initialization
    for adapter_cls in dbus_adapter:
        try:
            adapter = adapter_cls()
            return adapter
        except Exception:
            continue
    return None


def get_default_dbus_adapter() -> DbusAdapter | None:
    try:
        from wakepy.io.dbus.jeepney import JeepneyDbusAdapter
    except ImportError:
        return None
    return JeepneyDbusAdapter()
