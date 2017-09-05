#!/usr/bin/env python
from setuptools import setup

setup(
    name='manure',
    version='0.1.1',
    description="Very lightweight helper for producing analyis output at ISDC",
    author="Dominik Neise",
    author_email='neised@phys.ethz.ch',
    url='https://github.com/dneise/manure',
    py_modules=['manure'],
    install_requires=[
        'filelock>=2.0.7'
        'numpy',
        'pandas',
        'pyfact',
    ],
    license="MIT license",
    zip_safe=False,
)
