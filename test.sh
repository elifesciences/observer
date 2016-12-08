#!/bin/bash

set -e # everything must pass

. install.sh

. .lint.sh
. .test.sh
