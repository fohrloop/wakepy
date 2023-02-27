import io
import re
from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    io.open("wakepy/__init__.py", encoding="utf_8_sig").read(),
).group(1)

setup(
    name="wakepy",
    version=__version__,
    author="Niko Pasanen",
    author_email="niko@pasanen.me",
    url="https://github.com/np-8/wakepy",
    packages=find_packages(),
    include_package_data=True,
    license="MIT",
    description="Simple wakelock / keep-awake / stay-awake",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Topic :: Utilities",
    ],
    install_requires=[
        # Default install on linux uses jeepney
        # use --no-deps to skip if necessary
        "jeepney >= 0.7.1;sys_platform=='linux'",
    ],
    entry_points={
        "console_scripts": [
            "wakepy = wakepy.__main__:wakepy",
        ],
    },
)
