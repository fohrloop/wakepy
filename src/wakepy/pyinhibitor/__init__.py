"""This subpackage defines the python based inhibitor client and server.

With this package, it is possible to use python packages outside of your
current python environment (for example, directly from your system python
site-packages). The idea is to run a python server with the required packages
and communicate with it via a unix socket.

The server can only utilize "inhibitor modules", which are simple python
modules that define a class called Inhibitor. See the inhibitor_server.py
for the full specification.

This works only on unix-like systems (on systems which support unix sockets).
"""

from .inhibitors import get_inhibitor as get_inhibitor
