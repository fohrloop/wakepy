# Sleep vs Suspend vs Standby vs Hibernate?

So what does it mean when a computer goes to sleep? How it is sleep different from suspend or standby? Let's start by introducing the Advanced Configuration and Power Interface (ACPI) states, which are shown in the table below. The states are from the most active to the least active. 

| State | What it is                                                                           | CPU           | RAM          |
| ----- | ------------------------------------------------------------------------------------ | ------------- | ------------ |
| S0    | **Active State** = Working mode   (corresponds to S0i0 )                             | Active        | On           |
| S1    | **Quick Suspend to RAM**[1] = Power On Suspend (POS) = Power on Standby = Standby[2] | Clock stopped | Refreshed    |
| S2    | *(Not commonly     implemented)*                                                     | Power off     | Refreshed    |
| S3    | **Suspend to RAM** (STR) = Standby[3]                                                | Power off     | Slow refresh |
| S4    | **Suspend to Disk** (STD) = Hibernation                                              | Power off     | Off          |
| S5    | Soft Off                                                                             | Power off     | Off          |

\*[1] According to [acpi manual](https://manpages.ubuntu.com/manpages/xenial/en/man4/acpi.4freebsd.html) [2023-05-21]<br>
\*[2] According to  [wysocki2017].<br>
\*[3] According to [wiki-acpi]

### S0ix states
The s0ix states are called Suspend to Idle or S2I or S2Idle or S0 Low Power Idle or Modern Standby (by Microsoft) or Active Idle states. Not all platforms support these, and for example on  Windows, If a computer supports "Modern Standby" that is used instead of the traditional ACPI states S1-S3. [mslearn2020]
  
| State | What it is                                                                                                                                                                                                                                                                                                                                                                   | CPU     |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| S0i0  | The active state                                                                                                                                                                                                                                                                                                                                                             | Active  |
| S0i1  | Used during idle periods when user is actively using the device                                                                                                                                                                                                                                                                                                              | Depends |
| S0i3  | <ul><li>Deepest of S0ix states.</li><li>Used when user is not actively using the device. </li><li>Equivalent to S3 sleep, but explicitly allowed software activity may run [mslearn2020] </li><li> Desktop apps are stopped by the Desktop Activity Moderator (DAM); however, background tasks from Microsoft Store apps are permitted to do work.  [mslearn2020] </li></ul> | Depends |



## What happens when computer goes to standby / sleep / suspend / hibernation ?

### Standby


- Linux
  - Any / Ubuntu: This is the ACPI S1 state [wysocki2017, uwiki-us] 
  - Ubuntu: A state where programs continue running, but some components like the monitor is turned off. (*this is condadictory to above, where CPU is stopped*) [uwiki-pm]
  
### Sleep

- Windows 
  - On SoC systems that do not support Modern Standby:  One of the states ACPI S1-S3. Usually it is ACPI S3. Can be configured in BIOS/UEFI.  [dell-hiber, ml2023]
  - On SoC systems that support Modern Standby: One of the states S0i1-S0i3  [ml2023]
- Linux
  - This is usually called "Suspend" or "Suspend-to-idle"
### Suspend-to-idle

- Linux: This means the S0ix states (S0i1, S0i2 or S0i3) and only applicable to systems with specific hardware support (those systems do not have ACPI S1-S4 states).  [arch-pwr, wysocki2017]
- Windows: This is called "Sleep" 
  
### Suspend

- Linux 
  - Ubuntu: Suspend means suspend to RAM (ACPI S3) [uwiki-us].  Interestingly enough, one of the scripts called is named 'sleep': `/etc/pm/sleep.d`. ([source](https://askubuntu.com/a/9533/215022))
  - Arch Linux: Suspend means ACPI S3 [arch-pwr]
- Windows: This is called "Sleep"
  
### Hibernation 
- Any: This means suspend to disk (ACPI S4) regardless of operation system [ml2023, wiki-acpi, uwiki-us, wysocki2017]


## References


[arch-pwr] Arch Linux Wiki: Power management/Suspend and hibernate [[link](https://wiki.archlinux.org/title/Power_management/Suspend_and_hibernate)] (Accessed 2023-05-21)

[dell-hiber] dell.com: Windows 11 and Windows 10: Troubleshooting sleep and hibernation issues on your Dell Computer. [[link](https://www.dell.com/support/kbdoc/en-uk/000129843/windows-10-troubleshooting-sleep-hibernation-issues-on-your-dell-pc)]

[mslearn2020] Microsoft Learn (2020) Modern Standby vs S3 [[link](https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/modern-standby-vs-s3)]

[uwiki-pm] Ubuntu Wiki: Power Management. [[link](https://wiki.ubuntu.com/PowerManagement)] (Accessed 2023-05-20)

[uwiki-us] Ubuntu Wiki: Understanding Suspend. [[link](https://wiki.ubuntu.com/UnderstandingSuspend)] (Accessed 2023-05-20)

[wiki-acpi] Wikipedia: ACPI. [[link](https://en.wikipedia.org/wiki/ACPI)] (Accessed 2023-05-17)

[ml2023] learn.microsoft.com (2023) System power states  [[link](https://learn.microsoft.com/en-us/windows/win32/power/system-power-states)]

[wysocki2017] Wysocki (2017) System Sleep States. kernel.org [[link](https://www.kernel.org/doc/html/v4.18/admin-guide/pm/sleep-states.html#standby)]


