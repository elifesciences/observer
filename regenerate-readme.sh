#!/bin/bash
# regenerates the README.md document.
# the sections on available reports are generated from actual report definitions.

source venv/bin/activate
./src/manage.py readme > README.md
