#!/bin/bash
# convenience wrapper around Django's runserver command
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR
source install.sh
exec ./src/manage.py $@
