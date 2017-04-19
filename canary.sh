#!/bin/bash

# everything must pass
set -e

# reload the virtualenv
rm -rf venv/
virtualenv --python=`which python3.5` venv
source venv/bin/activate
pip install -r requirements.txt

# upgrade all deps to latest version
pip install pip-review
pip-review --pre # preview the upgrades
echo "[any key to continue ...]"
read -p "$*"
pip-review --auto --pre # update everything

pip freeze > new-requirements.txt

# run the tests
python src/manage.py migrate
./src/manage.py test src/
