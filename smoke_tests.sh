#!/bin/bash
set -ex

for path in / /report/latest-articles /report/upcoming-articles; do
    hostname=$(hostname)
    if [[ "$hostname" == "ci--observer.elifesciences.org" ]]; then
        hostname="ci-observer.elifesciences.org"
    fi
    [ $(curl --write-out %{http_code} --silent --output /dev/null https://$hostname$path) == 200 ]
done

