# Sleep vs Suspend vs Standby vs Hibernate?

So what does it mean when a computer goes to sleep? How it is sleep different from suspend or standby? Let's start by introducing the Advanced Configuration and Power Interface (ACPI) states.

### Advanced Configuration and Power Interface (ACPI) States

The table below shows the different ACPI states. The states are from the most active to the least active. Note that the *Standby* state can mean bit different things for different people, but people seem to agree that it is a state where computer is suspended into RAM.
| State | What it is                                               | CPU           | Ram |
| ----- | -------------------------------------------------------- | ------------- | --- |
| S0    | **Active State** = Working mode   (corresponds to S0i0 ) | Active        | On  |
| S1    | Power On Suspend = (POS) = Standby[1]                    | Clock stopped | On  |
| S2    |                                                          | Power off     | On  |
| S3    | **Suspend to RAM** (STR) = Standby[2]                    | Power off     | On  |
| S4    | **Suspend to Disk** (STD) = Hibernation                  | Power off     | Off |
| S5    | Soft Off                                                 | Power off     | Off |

\*[1] According to  [wysocki2017].<br>
\*[2] According to [wikipedia](https://en.wikipedia.org/wiki/ACPI) [2023-05-17]


### S0ix states
The s0ix states are called Suspend to Idle or S2I or S2Idle or S0 Low Power Idle or Modern Standby (by Microsoft) or Active Idle states. Not all platforms support these, and for example on  Windows, If a computer supports "Modern Standby" that is used instead of the traditional ACPI states S1-S3. [mslearn2020]
  
| State | What it is                                                                                                                                                                                                                                                                                                                                                                   | CPU     |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| S0i0  | The active state                                                                                                                                                                                                                                                                                                                                                             | Active  |
| S0i1  | Used during idle periods when user is actively using the device                                                                                                                                                                                                                                                                                                              | Depends |
| S0i3  | <ul><li>Deepest of S0ix states.</li><li>Used when user is not actively using the device. </li><li>Equivalent to S3 sleep, but explicitly allowed software activity may run [mslearn2020] </li><li> Desktop apps are stopped by the Desktop Activity Moderator (DAM); however, background tasks from Microsoft Store apps are permitted to do work.  [mslearn2020] </li></ul> | Depends |



## What happens when computer goes to sleep / suspend?


### Windows
 Systems typically support one of the states (S1, S2 or S3), not all three. So, a "Sleep" action maps to one of the states S1-S3 [dell-hiber]. Usually it is CPU state S3. Can be configured in BIOS/UEFI. 




## References

[dell-hiber] dell.com: Windows 11 and Windows 10: Troubleshooting sleep and hibernation issues on your Dell Computer. [[link](https://www.dell.com/support/kbdoc/en-uk/000129843/windows-10-troubleshooting-sleep-hibernation-issues-on-your-dell-pc)]

[mslearn2020] Microsoft Learn (2020) Modern Standby vs S3 [[link](https://learn.microsoft.com/en-us/windows-hardware/design/device-experiences/modern-standby-vs-s3)]

[wysocki2017] Wysocki (2017) System Sleep States. kernel.org [[link](https://www.kernel.org/doc/html/v4.18/admin-guide/pm/sleep-states.html#standby)]