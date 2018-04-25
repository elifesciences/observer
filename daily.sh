#!/bin/bash
# called by a cron jobm, daily

./manage.sh load_from_api --target profiles elife-metrics
