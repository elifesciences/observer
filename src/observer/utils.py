from dateutil import parser
from datetime import datetime
import pytz

import logging
LOG = logging.getLogger(__name__)

def isint(v):
    try:
        int(v)
        return True
    except (ValueError, TypeError):
        return False

def gmap(fn, lst):
    return list(map(fn, lst))

def todt(val):
    "turn almost any formatted datetime string into a UTC datetime object"
    if val == None:
        return None

    if not isinstance(val, datetime):
        dt = parser.parse(val, fuzzy=False)
    else:
        dt = val # don't attempt to parse, work with what we have

    if not dt.tzinfo:
        # no timezone (naive), assume UTC and make it explicit
        LOG.debug("encountered naive timestamp %r from %r. UTC assumed.", dt, val)
        return pytz.utc.localize(dt)

    else:
        # ensure tz is UTC
        if dt.tzinfo != pytz.utc:
            LOG.debug("got an aware dt that isn't in utc: %r", dt)
            return dt.astimezone(pytz.utc)
    return dt

def subdict(dt, ks):
    "returns a copy of the given dictionary `dt` with only the keys `ks` included"
    return {k:v for k, v in dt.items() if k in ks}
