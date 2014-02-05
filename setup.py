#!/usr/bin/env python

from setuptools import setup
import sys
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name='smw',
    license='License :: OSI Approved :: Python Software Foundation License',
    #py_modules=['foobar', ],
    packages=['smw'],
    version='0.1',
    install_requires=[
        'mwclient>=0.7dev',
        'rdflib',
        'beautifulsoup4'
        ],
    dependency_links=[
        "git+https://github.com/mwclient/mwclient.git@master#egg=mwclient-0.7dev"
        ],
    #tests_require=['pytest','pytest-xdist'],
    cmdclass={'test': PyTest},

    description='Semantic Mediawiki Python Binding',
    long_description=open('README.txt').read(),

    author='Jie Bao',
    author_email='baojie@gmail.com',
    url='https://github.com/baojie/smw',

    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Python Software Foundation License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
    ]
)
