# Mode activation

***TODO**: This page is WIP. Update after code for activating a mode mode is written.*

Activating a Mode is a three-stage process. With each Method, in the order of priority, wakepy:
1. Checks platform support
2. Checks requirements
3. Tries to activate a Mode using the Method

If `max_methods` is not `None` and number of successful Mode activations reaches `max_methods`, no more methods are tried. Otherwise, all Methods of the Mode are tried.

:::{figure} ./img/methods-after-check-platform.svg 
:width: 800px
:name: fig-methods-after-check-platform
:alt: wakepy mode activation check platform

*Methods divided by outcome after checking platform support*
:::