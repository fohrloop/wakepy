# Old Technical details (remove these)


When entering into a Mode, a lot of things occur. One of the things is that wakepy needs to determine, from all the [***Methods***](#wakepy-methods) in `Mode.methods`, which ones can be used. There might be multiple reasons why a method could not be used
- Wrong operating system or platform
- Wrong Desktop Environment
- Required software not found
- Wrong version of Desktop Environment or software





## Wakepy Mode Lifecycle

The Wakepy Mode lifecycle is shown in the [Figure](#fig-mode-phases) below. Everything starts with the `Mode.enter()` call in the main thread. All the `Mode.methods` are optionally prioritized using the user-supplied list of prioritized methods. Then, a new thread is spawn. Threads are needed for the support of all "heartbeat" type of methods, but they also make entering the mode faster, which is nice if there are many candidate methods available. This way user code does not need to wait at all when entering a mode.

In the new thread, suitability of each method is checked. In this phase filter out all methods that require different OS than what the code is running on. Also, use the `method.check_suitability()` to check other things. For example, some methods might require certain desktop environment or other software of certain version to be present. At this stage, possible known bugs of 3rd party software on certain versions can be acted on.



:::{figure} ./img/wakepy-mode-lifecycle.svg 
:w: 300px
:name: fig-mode-phases
:alt: wakepy mode phases

*Wakepy mode lifecycle*
:::

Then, with all the methods which are suitable or potentially suitable (`method.suitability` is not `UNSUITABLE`), try `method.enter_mode()` *and* `method.heartbeat()`. Set the `method.entered` and `method.success` attributes of each of the non-unsuitable methods. If the method implements a good `.check_suitability`, it will most probably succeed. If you wonder why the `method.heartbeat()` is called at this stage, here's the reason: that will allow different entry strategies, like: *use just first successful method* or *use N first successful methods* in addition to the *use all possible methods*.

Then is the first possible moment to communicate back to the main thread (to ModeManager) the end result of the mode activation: Did it succeed? Which methods were used? Etc. So that is done here. If any properties/methods of `ModeManager` requiring this information are accessed in the Main Thread before this information is available, that function call *blocks* until the information is available.

After communication to the main thread, the worker thread will 
- if there are any successful methods using heartbeat, start the heartbeat loop
- if there are no successful methods using heartbeat, but `enter_mode()`, just *block* and wait until user exits the mode (zero resource usage)
- if all methods failed, simply exit.

When the context manager is exited, a `EXIT` command is automatically sent from main thread to the worker thread, which either exits the heartbeat loop or stops the wait (depending on the state), and exits with `method.exit_mode()` using all the active methods.  After this, the thread terminates.

(wakepy-methods)=
## Wakepy Methods

**Methods** are different ways of entering/keeping in a Mode. A Method may support one or more platforms, and may have one or more requirements for software it should be able to talk to or execute. For example, on Linux. using the Inhibit method of the [org.gnome.SessionManager](https://lira.no-ip.org:8443/doc/gnome-session/dbus/gnome-session.html) D-Bus service is one way of entering `keep.running` mode, and it required D-Bus and (a certain version of) GNOME. 

