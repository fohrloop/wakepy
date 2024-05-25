<!-- start before docs link -->
![GitHub tag (latest by date)](https://img.shields.io/github/v/tag/fohrloop/wakepy)&nbsp;![PyPI](https://img.shields.io/pypi/v/wakepy)&nbsp;![PyPI - Downloads](https://img.shields.io/pypi/dm/wakepy)&nbsp;![GitHub](https://img.shields.io/github/license/fohrloop/wakepy)

# ⏰😴 wakepy

Cross-platform wakelock / keep-awake / stay-awake written in Python.

## Supports
- Python: 3.7 to 3.13
- OS: Windows, Linux and macOS

## What it can do?

Wakepy has two main modes:
1. **`keep.running`**: keep your tasks & CPU running even if you lock your session and turn screenlock on; This mode prevents your system from going to sleep automatically (*e.g.* for training machine learning models, video encoding, web scraping, ...)
2. **`keep.presenting`**: same as `keep.running` but keep also the screen awake and prevent automatic screen lock & screensaver  (*e.g.* for showing a video, updating dashboard, monitoring apps, ...)
<!-- end before docs link -->

> [!NOTE]
> Wakepy API is still experimental 🚧
> 
> Since wakepy is still 0.x.x, the API might change without further notice from
> one release to another. After that, breaking changes should occur only part of
> a major release (e.g. 1.x.x -> 2.0.0). 

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
- Supports multiple operating systems and desktop environments
- Simple command line interface and a python API
- Permissive MIT licence
- Low amount of python dependencies
  - For using the D-Bus methods on Linux: [jeepney](https://jeepney.readthedocs.io/)
  - On Python 3.7: [typing-extensions](https://pypi.org/project/typing-extensions/).
  - Otherwise: None


## Deprecation timeline (wakepy 0.7.0+)

Since deprecations may affect many users, they are communicated well before and time is given for project maintainers for migration. Timeline:

- **June 11th 2023**: Release wakepy 0.7.0 with DeprecationWarnings for keepawake, set_keepawake and unset_keepawake, and the CLI option -s. [Migration Guide](https://wakepy.readthedocs.io/v0.7.0/migration.html) published.
- **September 1st 2023** (*or few days later*): Release wakepy without the deprecated keepawake, set_keepawake and unset_keepawake; Only new API supported.


<!-- end after docs link -->

## Changelog

- See: https://wakepy.readthedocs.io/stable/changelog.html

