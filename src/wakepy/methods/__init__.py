"""This sub-package provides all types of methods for activating different
modes. The methods should be placed into modules with following rules. Pick
the module name from the first rule that is matches:

(1) If the method depends on certain desktop environment, it is listed in a
module named after the desktop environment. (Even if the method would have
additional dependencies)

(2) If the method depends on existence of some software or shared library, it
is listed in a module named after the software or shared library. In case of
multiple dependencies of this type, use the name of the "most specific" or
"least widespread" software.

Examples
(1) If a method needs D-Bus and GNOME, it is listed in gnome.py since GNOME is
    a desktop environment.
(2) If a method needs a hypothetical (not well known) programX and systemd and
    D-Bus, it is listed under programx.py, because programX is the "most
    specific" or "least widespread" software.
(3) If a method needs systemd and D-Bus, it is listed under systemd, as D-Bus
    is more widespread than systemd, and you may have D-Bus without systemd
    but not vice versa.
"""

# NOTE: All modules containing wakepy.Methods must be imported here! The reason
# is that the Methods are registered into the method registry only if the class
# definition is executed (if the module containing the Method class definition
# is imported)
from . import _testing as _testing
from . import freedesktop as freedesktop
from . import gnome as gnome
from . import macos as macos
from . import windows as windows
