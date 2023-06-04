# What is power management? 

Power Management is the software in a computer that switches the system to a low-power [sleep / standby / hibernation state](./sleep) when inactive. 

---------

## Windows

On Windows, power management is based on a idle timer. If the computer is idle longer time than the pre-set time, PC may be suspended automatically. The length of the timer can be set in the Settings:

-  System -> Power & sleep (Windows 10)
-  System -> Power & battery (Windows 11)

There are separate timers for the PC and the screen, and separate timers when running on battery and when plugged in.

### How to prevent Windows from suspending automatically?

- Applications may inhibit the idle timer with the [SetThreadExecutionState API](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate).
- See also: [System Sleep Criteria](https://learn.microsoft.com/en-us/windows/win32/power/system-sleep-criteria)
---------


## macOS

On macOS, power management is based on a idle timer. If the computer is idle longer time than the pre-set time, system may be suspended or the screen may be turned off automatically. The length of the timer can be set in the System Preferences.

### How to prevent macOS from suspending automatically?

- With [caffeinate](https://ss64.com/osx/caffeinate.html)

---------

## Linux


On Linux,  [power management](https://wiki.archlinux.org/title/Power_management)  is the responsibility of a *power manager*. Often times the power manager is the power management component of the used desktop environment.  However, it is possible that the used desktop environment does not have a power management component, and it is possible to use Linux without a desktop environment. In this case, the power manager is a separate application. 


### Desktop environments on Linux

Desktop environment can be thought of a GUI for your Linux. It is an interchangeable component and there are many alternatives, like 

- [GNOME](https://www.gnome.org/)
- [Plasma](https://kde.org/plasma-desktop/) (KDE)
- [Cinnamon](https://spins.fedoraproject.org/cinnamon/)
- [MATE](https://mate-desktop.org/)
- [LXQt](https://lxqt-project.org/)
- [Xfce](https://www.xfce.org/)
- [LXDE](http://www.lxde.org/)
  
Desktop Environment itself consists of a Window Manager and bunch of other stuff, like application menu, wallpaper, file manager, GUI theming, etc. Often the desktop environment has also a power management component. A DE is optional and many server-oriented Linux distros do not have a desktop environment by default. If a system does not have a desktop environment, and it runs without a GUI, it is called *headless*. 

#### GNOME

- When session is marked idle, *GNOME Power Manager* starts its own *system* timer. When the timeout set in `gnome-power-preferences` is reached, the idle action is performed (turn screen off / suspend / hibernate).

### How to prevent Linux from suspending automatically?

If the system uses systemd version 183+ (released May 2012), it will have [Inhibitor locks](https://www.freedesktop.org/wiki/Software/systemd/inhibit/) available through the logind D-Bus API. 


# References

[gnome] https://help.gnome.org/users/gnome-power-manager/stable/preferences.html.en