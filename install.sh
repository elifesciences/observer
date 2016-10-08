#!/bin/bash
set -e # everything must succeed.
if [ ! -d venv ]; then
    virtualenv --python=`which python3` venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

python src/manage.py migrate --no-input
