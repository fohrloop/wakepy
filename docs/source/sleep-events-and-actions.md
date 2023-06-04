# What causes computer to sleep?

There are multiple different reasons which may cause a computer to stop execution of a program and do something else, like sleep, hibernate or shutdown. These reasons are called on this page *events*. A system responds to these events by taking an *action*, which may be for example:

- [sleep](./sleep.md) (suspend to RAM / hibernate)
- shutdown
- turn screen off / turn screensaver on (blank screen)
- lock screen / lock session

Out of these only suspend and shutdown will cause the CPU to stop executing your program. Sometimes a combination of actions is taken, for example, locking screen, turning screen off and suspending to RAM.

## Events that may cause system to go to sleep
 There are multiple different types of events which *may* cause system to go to sleep. 

| #   | Event category                              | event details                           | Auto? |
| --- | ------------------------------------------- | --------------------------------------- | ----- |
| 1a  | Idle timer reaches a threshold              | on external power                       | Y     |
| 1b  |                                             | on battery                              | Y     |
| 2a  | Suspend action requested by user / program  | sleep requested                         | Y     |
| 2b  |                                             | suspend requested                       | Y     |
| 3a  | Shutdown action requested by user / program | shutdown requested                      | Y     |
| 3b  |                                             | reboot requested                        | Y     |
| 4a  | Laptop lid is closed                        | on external power                       | N     |
| 4b  |                                             | when docked or connected to > 1 display | N     |
| 4c  |                                             | otherwise                               | N     |
| 5a  | When a hardware key is pressed              | power key                               | N     |
| 5b  |                                             | sleep key                               | N     |
| 5c  |                                             | hibernate key                           | N     |
| 6a  | Battery charge                              | goes below a critical level             | Y     |


The only events which may happen automatically are
- Idle timer reaches pre-set time
- Suspend or shutdown action requested by program (e.g. through the idle timer reaching a specific threshold and some program automatically reacting on it)
- Battery draining below a critical level (on laptops when not connected to external power)

To prevent your program stopping execution, you want to inhibit (prevent) the automatic idle, suspend and shutdown actions. If battery drains below a critical level, it is advisable to let your computer go to a low-power state (suspend/hibernate/soft-off) to prevent any hardware damage.

