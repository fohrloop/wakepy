from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="wakepy",
    version="0.4.2",
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
        "Topic :: Utilities",
    ],
)
