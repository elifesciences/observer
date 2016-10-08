#!/bin/bash
set -e

# remove any old compiled python files
# pylint likes to lint them
find src/ -name '*.py[c|~]' -delete

echo "* calling pyflakes"
pyflakes ./src/
echo "* calling pylint"
pylint -E ./src/observer/** --load-plugins=pylint_django --disable=E1103
echo "* passed linting"
