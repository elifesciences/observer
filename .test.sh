#!/bin/bash
# run full or partial test suite:
#   ./.test.sh
# or
#   ./.test.sh observer.tests.test_rss_views

set -e

# quick check for syntax errors
pyflakes src/

args="$@"
module="src"
print_coverage=1
if [ ! -z "$args" ]; then
    module="$args"
    print_coverage=0
fi

# remove any old compiled python files that interfere with test discovery
find src/ -name '*.pyc' -delete

# run the tests
coverage run \
    --source='src/' \
    --omit='*/tests/*,*/migrations/*,src/core/settings.py,src/core/wsgi.py,src/manage.py,src/observer/apps.py' \
    src/manage.py test "$module" --no-input

# print test coverage
# BUT only if we're running a complete set of tests
if [ $print_coverage -eq 1 ]; then
    coverage report
    # is only run if tests pass
    covered=$(coverage report | grep TOTAL | awk '{print $4}' | sed 's/%//')
    if [ $covered -lt 79 ]; then
        coverage html
        echo
        echo -e "\e[31mFAILED\e[0m this project requires at least 80% coverage, got $covered"
        echo
        exit 1
    fi
fi
