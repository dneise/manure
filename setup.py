#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='manure',
    version='0.1.0',
    description="Very lightweight helper for producing analyis output e.g. at ISDC",
    author="Dominik Neise",
    author_email='neised@phys.ethz.ch',
    url='https://github.com/dneise/manure',
    py_modules=['manure'],
    install_requires=[
        'numpy',
        'pandas',
        'pyfact',
    ],
    license="MIT license",
    zip_safe=False,
)
