#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='pymfit',
      version='v0.1',
      author='Johnny Greco',
      author_email='jgreco@astro.princeton.edu',
      packages=['pymfit'],
      url='https://github.com/johnnygreco/pymfit',
      description='python wrapper for imfit')
