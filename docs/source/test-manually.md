# How to test wakepy Modes?

All wakepy Modes rely somehow on external software, library or dbus service. This is why it cannot be 100% guaranteed beforehand that a wakepy Mode can be activated on some specific platform and Desktop Environment, even if a particular Mode would have multiple alternative Methods. This page lists ways to check manually if wakepy mode works on a system.



```{admonition} Notes for manual testing
:class: warning
**Before testing**

- Close browser tabs which might prevent your system from going to sleep (e.g.  YouTube)
- Close applications which might prevent your system from going to sleep (e.g. video players apps)

**When ending the test**

- Avoid pressing the power button as it might force the computer to sleep.
```

## wakepy test script

This is a test script for helping to determine if the wakepy modes work correctly on your system:

(code-wakepy-test-script)=
```{code-block} python
import datetime as dt
import time

start = dt.datetime.now()
now = None
while True:
    prev = now or dt.datetime.now()
    now = dt.datetime.now()
    now_str = now.strftime("%b %d %H:%M:%S")
    delta_str = f"{(now-prev)/dt.timedelta(seconds=1)}s"
    print(f"{now_str} | elapsed {now-start} | delta: {delta_str}")
    time.sleep(2)
```

This will print something like:

```{code-block} output
Dec 25 12:28:34 | elapsed 0:00:00.000176 | delta: 2e-06s
Dec 25 12:28:36 | elapsed 0:00:02.000403 | delta: 2.000227s
Dec 25 12:28:38 | elapsed 0:00:04.001173 | delta: 2.00077s
Dec 25 12:28:40 | elapsed 0:00:06.001792 | delta: 2.000619s
Dec 25 12:28:42 | elapsed 0:00:08.002630 | delta: 2.000838s
Dec 25 12:28:44 | elapsed 0:00:10.003227 | delta: 2.000597s
Dec 25 12:28:46 | elapsed 0:00:12.004019 | delta: 2.000792s
Dec 25 12:28:48 | elapsed 0:00:14.004220 | delta: 2.000201s
Dec 25 12:28:50 | elapsed 0:00:16.004479 | delta: 2.000259s
Dec 25 12:29:10 | elapsed 0:00:35.483558 | delta: 19.479079s
Dec 25 12:29:12 | elapsed 0:00:37.484053 | delta: 2.000495s
Dec 25 12:29:14 | elapsed 0:00:39.484265 | delta: 2.000212s
Dec 25 12:29:16 | elapsed 0:00:41.484495 | delta: 2.00023s
Dec 25 12:29:18 | elapsed 0:00:43.484847 | delta: 2.000352s
Dec 25 12:29:20 | elapsed 0:00:45.485045 | delta: 2.000198s
```

In the above example, the delta (time between two prints) was 2 seconds, until 16 seconds elapsed. After that, CPU was sleeping for 19 seconds.

## Entering in wakepy modes for tests

(enter-keep-running-script)=
### keep.running

Either on CLI

```{code-block} text
wakepy
```

or in python


```{code-block} python
import time
from wakepy import keep
with keep.running():
    while True:
      time.sleep(1)
```

(enter-keep-presenting-script)=
### keep.presenting

Either on CLI

```{code-block} text
wakepy -p
```

or in python


```{code-block} python
import time
from wakepy import keep
with keep.presenting():
    while True:
      time.sleep(1)
```




## GNOME

- Homepage: [gnome.org](https://www.gnome.org/)

(gnome-keep-running-manual-test)=
### keep.running (GNOME)

Before you start. Check the current timeout values (seconds), and write the number down somewhere. The first one (org.gnome.desktop.session idle-delay) is time until "screen blank", and the rest are timeouts for automatic sleep.

```{code-block} text
gsettings get org.gnome.desktop.session idle-delay
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout
```

Then, set a low value to the timeouts (here, 15 seconds):

```{code-block} text
gsettings set org.gnome.desktop.session idle-delay 15
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 15
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 15
```

Test that your system sleeps automatically and blanks the screen after 15 seconds. Then, run the [wakepy test script](#code-wakepy-test-script) on one terminal window, and enter in the [keep.running](#enter-keep-running-script)  or in the in another. After you're done, reset the timeout values to what they were (in this example, 1800 seconds):

```{code-block} text
gsettings set org.gnome.desktop.session idle-delay 1800
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 1800
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 1800
```

### keep.presenting (GNOME)

Follow the [same steps as in with keep.running](#gnome-keep-running-manual-test), but enter the [keep.presenting](#enter-keep-presenting-script) mode


## Windows

(windows-keep-running-manual-test)=
### keep.running (Windows)

Change your current settings from windows menu -> "Edit Power Plan". Change "Turn off the display" and "Put the computer to sleep"  both to 1 minute. -> Save Changes.

Then, run the [wakepy test script](#code-wakepy-test-script) on one terminal window, and enter in the [keep.running](#enter-keep-running-script)  or in the in another. After you're done, reset the Power Plan values to what they were.


```{admonition} About Windows idle timers
:class: info
Note: Windows does not seem to always respect low values in the power settings. To make Windows sleep faster, if using laptop, disconnect the charging cable (use battery). A one minute setting might start the sleep after 1:50 to 2:30 minutes.
```

### keep.presenting (Windows)
Follow the [same steps as in with keep.running](#windows-keep-running-manual-test), but enter the [keep.presenting](#enter-keep-presenting-script) mode
