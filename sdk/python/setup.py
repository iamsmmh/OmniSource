"""Setup script for the OmniSource Python SDK.

The SDK is single-file (omnisource_sdk.py) and has no runtime dependencies,
so this setup script is intentionally minimal.
"""

from __future__ import annotations

from setuptools import setup, find_packages

setup(
    name="omnisource-sdk",
    version="1.0.0",
    description="Zero-dependency Python client for the public OmniSource API.",
    long_description=open("README.md", encoding="utf-8").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    py_modules=["omnisource_sdk"],
    python_requires=">=3.8",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
