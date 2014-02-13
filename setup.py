#!/usr/bin/env python

from setuptools import setup

setup(
    name='smw',
    license='License :: OSI Approved :: Python Software Foundation License',
    #py_modules=['foobar', ],
    packages=['smw'],
    version='0.1.3.2',
    install_requires=[
        'mwclient>=0.7dev',
        'rdflib',
        'beautifulsoup4',
        'enum'
        ],
    dependency_links=[
        "git+https://github.com/mwclient/mwclient.git@master#egg=mwclient-0.7dev"
        ],
    tests_require=[],
    cmdclass={},

    description='Semantic Mediawiki Python Binding',
    long_description=open('README.rst').read(),

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
