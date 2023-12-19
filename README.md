<!-- start before docs link -->
![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/np-8/wakepy)&nbsp;![PyPI](https://img.shields.io/pypi/v/wakepy)&nbsp;![PyPI - Downloads](https://img.shields.io/pypi/dm/wakepy)&nbsp;![GitHub](https://img.shields.io/github/license/np-8/wakepy)

# ⏰😴 wakepy 

  Simple cross-platform wakelock written in Python. Comes with python API and a single executable for CLI usage.


## Supports
- Python: 3.7 to 3.12 
- OS: Windows, Linux and macOS 

## What it can do? 
  - Prevent your system from going to sleep in the middle of a long running task (e.g. training machine learning models, video encoding, web scraping, ...) 
  - Prevent starting a screensaver or screenlock automatically (showing a video, updating dashboard, monitoring apps, ...)
<!-- end before docs link -->



## Used by
- [viskillz-blender](https://github.com/viskillz/viskillz-blender) — Generating assets of Mental Cutting Test exercises
- [mpc-autofill](https://github.com/chilli-axe/mpc-autofill) — Automating MakePlayingCards' online ordering system
- [lakeshorecryotronics/python-driver](https://github.com/lakeshorecryotronics/python-driver) — Lake Shore instruments python Driver
- [UCSD-E4E/baboon-tracking](https://github.com/UCSD-E4E/baboon-tracking) — In pipelines of a Computer Vision project tracking baboons  
- [davlee1972/upscale_video](https://github.com/davlee1972/upscale_video) — Upscaling video using AI 
- [minarca](https://github.com/ikus060/minarca) — Cross-platform data backup software
## Documentation 
### 👉 **[wakepy.readthedocs.io](http://wakepy.readthedocs.io)**
<!-- start after docs link -->
## ⚖️👑 Key selling points
- Wakepy supports multiple operating systems and desktop environments
- Wakepy has permissive MIT licence
- It has a simple command line interface and a python API
- Wakepy has very little python dependencies:
  - Zero if using Windows or macOS or Linux + systemd
  - One if using linux + [jeepney](https://jeepney.readthedocs.io/) or linux + [dbus-python](https://dbus.freedesktop.org/doc/dbus-python/).


## Deprecation timeline (wakepy 0.7.0+) 

Since deprecations may affect many users, they are communicated well before and time is given for project maintainers for migration. Timeline:

- **June 11th 2023**: Release wakepy 0.7.0 with DeprecationWarnings for keepawake, set_keepawake and unset_keepawake, and the CLI option -s. [Migration Guide](https://wakepy.readthedocs.io/en/v0.7.2/migration.html) published.
- **September 1st 2023** (*or few days later*): Release wakepy without the deprecated keepawake, set_keepawake and unset_keepawake; Only new API supported.



<!-- end after docs link -->

