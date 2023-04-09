# Wakepy and Linux

## Debugging D-Bus

Wakepy >= 0.6.0 uses by default the Inhibit/Uninhibit methods of the  [org.freedesktop.Screensaver](https://specifications.freedesktop.org/idle-inhibit-spec/latest/re01.html) interface of the session D-Bus.

### Checking if dbus is running

The dbus daemon executable is `usr/bin/dbus-daemon`. If it is running, you should see it in the list of processes with Process Status (ps):
```
niko@niko-ubuntu-home:~/tmp/repos/wakepy$ ps -x  | grep dbus
   1107 ?        Ss     0:01 /usr/bin/dbus-daemon --session --address=systemd: --nofork --nopidfile --systemd-activation --syslog-only
   1246 ?        S      0:00 /usr/bin/dbus-daemon --config-file=/usr/share/defaults/at-spi2/accessibility.conf --nofork --print-address 11 --address=unix:path=/run/user/1000/at-spi/bus
  11415 pts/0    S+     0:00 grep --color=auto dbus
```

The [dbus-daemon](https://dbus.freedesktop.org/doc/dbus-daemon.1.html) docs explain that `--session` implies `"--config-file=/usr/share/dbus-1/session.conf"`. This is the session message bus.


### Getting the address of the session message bus

The address of the login session message bus is typically given in an environment variable, but there are other places which could also contain the bus address. These are, from highest to lowest precedence [Source: [D-Bus Specification](https://dbus.freedesktop.org/doc/dbus-specification.html)]: 


<ol type="a">
  <li> The DBUS_SESSION_BUS_ADDRESS environment variable. </li>
  <li>X Window System root window property _DBUS_SESSION_BUS_ADDRESS</li>
  <li>File located in the current user's home directory, in subdirectory .dbus/session-bus/</li>
</ol>



**Note**: If running inside subprocess (e.g. using tox + pytest), you need to make sure 
that the environment variable `DBUS_SESSION_BUS_ADDRESS` is passed from the parent
process. In tox, this is done using `pass_env`.

#### Other ways to get DBUS_SESSION_BUS_ADDRESS
If the environment variable is not set, you might see the address with:

- First, checking the process id of the session message bus daemon
- Then, reading the environment variables of that pid

For example:
```
niko@niko-ubuntu-home:~$ ps -x | grep dbus
   1107 ?        Ss     0:04 /usr/bin/dbus-daemon --session --address=systemd: --nofork --nopidfile --systemd-activation --syslog-only
   1246 ?        S      0:00 /usr/bin/dbus-daemon --config-file=/usr/share/defaults/at-spi2/accessibility.conf --nofork --print-address 11 --address=unix:path=/run/user/1000/at-spi/bus
  20247 pts/3    S+     0:00 grep --color=auto dbus

niko@niko-ubuntu-home:~$ cat /proc/1107/environ |  tr '\0' '\n' | grep DBUS_SESSION_BUS_ADDRESS
DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
```





