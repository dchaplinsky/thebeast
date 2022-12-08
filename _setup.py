#!/usr/bin/env python
# -*- coding: utf-8 -*-


from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()


test_requirements = [
    # TODO: put package test requirements here
    "pytest"
]

setup(
    name="thebeast",
    version="0.9.0",
    description="",
    python_requires=">=3.8",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dmitro Chaplynskyi",
    author_email="chaplinsky.dmitry@gmail.com",
    url="https://github.com/dchaplinsky/thebeast",
    packages=find_packages("thebeast"),
    package_dir={"": "thebeast"},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords="FollowTheMoney,FTM,data mapping,data engineering",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Typing :: Typed",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    test_suite="tests",
    tests_require=test_requirements,
    package_data={"": ["thebeast/tests/sample/mappings/*"]},
)
