from os import path
from setuptools import setup, find_packages
from codecs import open

NAME = "gha_datasets"

with open(
    path.join(path.abspath(path.dirname(__file__)), "README.md"), encoding="utf-8"
) as f:
    long_description = f.read()

setup(
    name=NAME,
    version="1.0.0",
    # license="LGPLv3",
    author="Guillaume Cardoen",
    url="https://github.com/cardoeng/msr2024_guillaume",
    description="A tool for extracting GitHub Actions workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="gha workflows dataset",
    packages=find_packages(include=[NAME]),
    python_requires="~= 3.8",
    install_requires=[
        "click ~= 8.1.7",
        "GitPython ~= 3.1.37",
    ],
    zip_safe=True,
    entry_points={"console_scripts": [f"gha-datasets={NAME}.main:main"]},
)
