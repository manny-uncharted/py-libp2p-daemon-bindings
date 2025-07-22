#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


def get_version() -> str:
    path = os.path.join(os.path.dirname(__file__), "p2pclient/__init__.py")
    with open(path, "r") as f:
        version_file = f.read()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


extras_require = {
    "test": [
        "mypy>=1.17.0",
        "pytest-cov>=2.12.0,<5.0.0",
        "pytest>=6.2.0,<8.0.0",
        "types-protobuf",
    ],
    "lint": [
        "black>=25.1.0",
        "flake8>=7.3.0",
        "isort>=6.0.1",
        "mypy-protobuf>=1.16",
    ],
    "dev": ["tox>=3.13.2,<4.0.0", "wheel"],
}

extras_require["dev"] = (
    extras_require["test"] + extras_require["lint"] + extras_require["dev"]
)


setuptools.setup(
    name="p2pclient",
    version=get_version(),
    author="Kevin Mai-Hsuan Chia",
    author_email="kevin.mh.chia@gmail.com",
    description="The libp2p daemon bindings for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mhchia/py-libp2p-daemon-bindings",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "anyio>=3.0.0,<4.0.0",
        "async-exit-stack>=1.0.1,<2.0.0",
        "async-generator>=1.10,<2.0",
        "base58>=1.0.3",
        "multiaddr>=0.0.8,<0.1.0",
        "protobuf>=3.9.0",
        "pycryptodome>=3.0.0,<4.0.0",
        "pymultihash>=0.8.2",
    ],
    extras_require=extras_require,
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
