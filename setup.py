#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import nodeeditor
from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read()

setup_requirements = []

test_requirements = []


setup(
    author="Azad Kshitij",
    author_email='azadkshitij08302001@gmail.com',
    classifiers=[
        'Development Status :: 1 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    description="Python Node Editor using PyQt5",
    install_requires=requirements,
    license="MIT license",
    long_description="provides full framework for creating customizable graph, nodes, sockets and edges. Full support for undo / redo and serialization into files in a VCS friendly way. Support for implementing evaluation logic. Hovering effects, dragging edges, cutting lines and a bunch more. Provided 2 examples on how node editor can be implemented",
    include_package_data=True,
    keywords='nodeeditor',
    name='nodeeditor',
    # packages=find_packages(include=['_template']),
    packages=find_packages(
        include=['nodeeditor*'], exclude=['examples*', 'tests*']),
    package_data={'': ['qss/*']},
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/AzadKshitij/qtpy-nodeeditor.git',
    version=nodeeditor.__version__,
    zip_safe=False,
)
