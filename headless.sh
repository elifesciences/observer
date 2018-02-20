#!/bin/bash
# for long-running processes
set -e

exec venv/bin/python src/manage.py $@
