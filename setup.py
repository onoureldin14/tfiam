#!/usr/bin/env python3

from setuptools import setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="tfiam",
    version="1.0.0",
    author="TFIAM - Terraform IAM Analyzer",
    description="TFIAM - Analyze Terraform repositories and generate IAM permission recommendations with AI explanations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["main"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "tfiam=main:main",
        ],
    },
)
