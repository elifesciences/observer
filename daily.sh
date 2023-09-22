#!/bin/bash
# refreshes specific content types daily.
# called by a cron job in observer-formula.
# other content types (articles, presspackages, digests, etc) are updated via the message bus.
# `load_from_api` is able to do adhoc imports of any content though.

./manage.sh load_from_api --target profiles elife-metrics community reviewed-preprints
./manage.sh load_from_api --target lax --days 2
