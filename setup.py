#!/usr/bin/env python
from distutils.core import setup


setup(
    name='cicreo',
    version='0.1',
    packages=[
        'cicero',
        'cicero.filters',
        'cicero.management',
        'cicero.management.commands',
        'cicero.templatetags',
        'cicero.utils',
    ],

    package_data={
        'cicero': ['templates/cicero/*']
    },

    author='Ivan Sagalaev',
    author_email='Maniac@SoftwareManiacs.org',
    description='Simple but powerfull forum django app',
    url='http://softwaremaniacs.org/soft/cicero/source/',
)
