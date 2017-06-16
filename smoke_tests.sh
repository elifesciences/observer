#!/bin/bash
set -ex

for path in / /report/latest-articles /report/upcoming-articles; do
    [ $(curl --write-out %{http_code} --silent --output /dev/null https://$(hostname)$path) == 200 ]
done

