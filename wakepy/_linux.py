try:
    import dbus, os, psutil
except ImportError as e:
    print(f'Error when importing DBus, os and psutil module: {e}\n\
Root permissions will be needed to set/unset the wakelock!')
import subprocess

COMMAND = u"systemctl"
ARGS = [u"sleep.target", u"suspend.target", u"hibernate.target", u"hybrid-sleep.target"]
# https://www.man7.org/linux/man-pages/man1/systemctl.1.html

dbus_inhibit = None  # Variable that stores the DBus inhibit for later controlled release.
try: # Try to initialize the freedesktop inhibitor
    pm_interface = dbus.Interface(dbus.SessionBus().get_object('org.freedesktop.ScreenSaver','/org/freedesktop/ScreenSaver'), 'org.freedesktop.ScreenSaver')
except Exception as e1:
    print(f"Wakepy can't use DBus Inhibit on this system because of a {type(e1).__name__}: {e1}\n\
root permissions will be needed to set/release the wakelock.")

try:
    subprocess.check_output(["pidof", "systemd"])
except subprocess.CalledProcessError:
    # if 'pidof' does not find a process it will return with non-zero exit status, check_output will raise subprocess.CalledProcessError
    # See: https://github.com/np-8/wakepy/pull/3
    raise NotImplementedError(
        "wakepy has not yet support for init processes other than systemd. Pull requests welcome: https://github.com/np-8/wakepy"
    )


def set_keepawake(keep_screen_awake=False):
    """
    Set the keep-awake. During keep-awake, the CPU is not allowed to go to sleep
    automatically until the `unset_keepawake` is called.

    Parameters
    -----------
    keep_screen_awake: bool
        Currently unused as the screen will remain active as a byproduct of preventing sleep.
    """
    try:
        global dbus_inhibit
        dbus_inhibit = pm_interface.Inhibit(psutil.Process(os.getpid()).name(), f'wakepy.set_keepawake(keep_screen_awake={keep_screen_awake})')
        # print(power_manager.HasInhibit()) # Prints out if the inhibitor is set ot not. 
    except Exception as e:
        print(f"DBus Inhibit failed with a {type(e).__name__}: {e}\nFalling back to systemctl mask...")
        subprocess.run([COMMAND, u"mask", *ARGS])


def unset_keepawake():
    try:
        pm_interface.UnInhibit(dbus_inhibit)
    except Exception as e:
        print(f"DBus Inhibit failed with a {type(e).__name__}: {e}\nFalling back to systemctl mask...")
        subprocess.run([COMMAND, u"unmask", *ARGS])
