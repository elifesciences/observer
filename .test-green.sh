#!/bin/bash

set -e # everything must pass

pyflakes src/

args="$@"
module="src"
print_coverage=1
if [ ! -z "$args" ]; then
    module="src.$args"
    print_coverage=0
fi

# remove any old compiled python files
find src/ -name '*.pyc' -delete
GREEN_CONFIG=.green ./src/manage.py test "$module" --testrunner=green.djangorunner.DjangoRunner --no-input -v 3
