#!/usr/bin/env python
"""
django-static-compiler
======================

An extension for Sentry which allows setting hard quotas.

:copyright: (c) 2013 by David Cramer.
:license: Apache License 2.0, see LICENSE for more details.
"""
from setuptools import setup, find_packages


tests_require = [
    'exam',
    'mock',
    'pytest',
    'pytest-django',
    'unittest2',
]

install_requires = [
    'django',
]

setup(
    name='django-static-compiler',
    version='0.3.3',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/dcramer/django-static-compiler',
    description='A static file compiler for Django',
    long_description=__doc__,
    license='Apache License 2.0',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    zip_safe=False,
    install_requires=install_requires,
    extras_require={'tests': tests_require},
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
