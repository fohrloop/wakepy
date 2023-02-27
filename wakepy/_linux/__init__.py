from importlib import import_module
from wakepy.exceptions import NotSupportedError


for module in "_dbus", "_systemd":
    try:
        my_module = import_module(f".{module}", f"wakepy._linux")
        set_keepawake, unset_keepawake = (
            my_module.set_keepawake,
            my_module.unset_keepawake,
        )
        break
    except NotSupportedError:
        pass
else:
    raise NotImplementedError(
        "wakepy does only support dbus and systemd based solutions "
        "Pull requests welcome: https://github.com/np-8/wakepy"
    )
