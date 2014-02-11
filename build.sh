#!/bin/bash
python setup.py build
pandoc -t rst README.md -o README.rst
python setup.py sdist
python setup.py bdist_egg
python setup.py sdist upload
python setup.py bdist_egg upload
