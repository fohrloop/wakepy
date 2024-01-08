(wakepy-methods)=
# Wakepy Methods 

## What are wakepy Methods?
**Methods** are different ways of entering/keeping in a Mode. A Method may support one or more platforms, and may have one or more requirements for software it should be able to talk to or execute. For example, on Linux. using the Inhibit method of the [org.gnome.SessionManager](https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html) D-Bus service is one way of entering  the [`keep.running`](#keep-running-section) mode, and it required D-Bus and (a certain version of) GNOME. 

(keep-running-section)=
## keep.running

(keep-running-org-gnome-sessionmanager)=
#### D-Bus: org.gnome.SessionManager
- **Name**: `org.gnome.SessionManager:Inhibit:Suspend`
- **Introduced in**: wakepy 0.8.0
- **How it works**: Uses the [Inhibit](https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html#org.gnome.SessionManager.Inhibit) method of [org.gnome.SessionManager](https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html#org.gnome.SessionManager) D-Bus service with flag 4 ("Inhibit suspending the session or computer") when activating and saves the returned cookie on the Method instance. Uses the [Uninhibit](https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html#org.gnome.SessionManager.Uninhibit) method of the org.gnome.SessionManager with the cookie when deactivating.  
- **Multiprocess safe?**: Yes
- **What if the process holding the lock dies?**: The lock is automatically removed.
- **How to check it?**:  You may check the list of inhibitors using the [GetInhibitors](https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html#org.gnome.SessionManager.GetInhibitors) method, which gives you list of object paths like `["/org/gnome/SessionManager/Inhibitor20"]`. Then you can use the [GetAppId](https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html#org.gnome.SessionManager.Inhibitor.GetAppId), [GetFlags](https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html#org.gnome.SessionManager.Inhibitor.GetFlags) and [GetReason](https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html#org.gnome.SessionManager.Inhibitor.GetReason) methods on the [org.gnome.SessionManager.Inhibitor](https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html#org.gnome.SessionManager.Inhibitor) interface of the listed objects on the org.gnome.SessionManager service to translate that into something meaningful. A good tool for this is [D-Spy](https://apps.gnome.org/Dspy/). Alternatively, you could monitor your inhibit call with [`dbus-monitor`](https://dbus.freedesktop.org/doc/dbus-monitor.1.html).
- **Requirements**: D-Bus, GNOME Desktop Environment with gnome-session running. The exact version of required GNOME is unknown, but this should work from GNOME 2.24 ([2008-09-23](https://gitlab.gnome.org/GNOME/gnome-session/-/tags/GNOME_SESSION_2_24_0)) onwards. See [version history of org.gnome.SessionManager.xml](https://gitlab.gnome.org/GNOME/gnome-session/-/commits/main/gnome-session/org.gnome.SessionManager.xml). At least [this](https://fedoraproject.org/wiki/Desktop/Whiteboards/InhibitApis) and [this](https://bugzilla.redhat.com/show_bug.cgi?id=529287#c3) mention GNOME 2.24.
- **Tested on**:  Ubuntu 22.04.3 LTS with GNOME 42.9 ([PR #138](https://github.com/fohrloop/wakepy/pull/138) by [fohrloop](https://github.com/fohrloop/)).


## keep.presenting

#### D-Bus: org.gnome.SessionManager

- **Name**: `org.gnome.SessionManager:Inhibit:Idle`
- **Introduced in**: wakepy 0.8.0
- **How it works**: Exactly the same as the [keep.running](#keep-running-org-gnome-sessionmanager) using org.gnome.SessionManager, but using the flag 8 ("Inhibit the session being marked as idle").
- **Multiprocess safe?**: Yes
- **What if the process holding the lock dies?**: The lock is automatically removed.
- **How to check it?**: Similarly as checking [keep.running](#keep-running-org-gnome-sessionmanager) using org.gnome.SessionManager.
- **Requirements**: Same as [keep.running](#keep-running-org-gnome-sessionmanager) using org.gnome.SessionManager.
- **Tested on**:  Ubuntu 22.04.3 LTS with GNOME 42.9 ([PR #138](https://github.com/fohrloop/wakepy/pull/138) by [fohrloop](https://github.com/fohrloop/)).