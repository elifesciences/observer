#!/bin/bash
set -e

# remove any old compiled python files
# pylint likes to lint them
#find src/ -name '*.py[c|~]' -delete
# http://stackoverflow.com/questions/28991015/python3-project-remove-pycache-folders-and-pyc-files
find . \( -name \*.pyc -o -name \*.pyo -o -name __pycache__ \) -prune -exec rm -rf {} +

echo "* calling pyflakes"
pyflakes ./src/
echo "* calling pylint"
pylint -E ./src/observer/** --load-plugins=pylint_django --disable=E1103
echo "* passed linting"
