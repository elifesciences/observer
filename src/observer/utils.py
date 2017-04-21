import os
from os.path import join
import copy
from dateutil import parser
from datetime import datetime
import pytz
import itertools
import logging
LOG = logging.getLogger(__name__)

def listfiles(path, ext_list=None):
    "returns a list of absolute paths for given dir"
    path_list = map(lambda fname: os.path.abspath(join(path, fname)), os.listdir(path))
    if ext_list:
        path_list = filter(lambda path: os.path.splitext(path)[1] in ext_list, path_list)
    return sorted(filter(os.path.isfile, path_list))


def isint(v):
    try:
        int(v)
        return True
    except (ValueError, TypeError):
        return False

lmap = lambda func, *iterable: list(map(func, *iterable))
lfilter = lambda func, *iterable: list(filter(func, *iterable))

def todt(val):
    "turn almost any formatted datetime string into a UTC datetime object"
    if val is None:
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
    return {k: v for k, v in dt.items() if k in ks}


# http://stackoverflow.com/questions/7204805/dictionaries-of-dictionaries-merge/7205107#7205107
def _merge(a, b, path=None):
    "merges b into a"
    if path is None:
        path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                _merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                # conflict, a gets it's key overridden
                a[key] = b[key]
                #raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a

def deepmerge(a, b, path=None):
    "merges 'b' into a copy of 'a'"
    a = copy.deepcopy(a)
    return _merge(a, b, path)


def to_dict(instance):
    from django.db.models.fields.related import ManyToManyField
    opts = instance._meta
    data = {}
    for f in opts.concrete_fields + opts.many_to_many:
        if isinstance(f, ManyToManyField):
            if instance.pk is None:
                data[f.name] = []
            else:
                data[f.name] = list(f.value_from_object(instance).values_list('pk', flat=True))
        else:
            data[f.name] = f.value_from_object(instance)
    return data


def renkey(ddict, oldkey, newkey):
    "renames a key in ddict from oldkey to newkey"
    if oldkey in ddict:
        ddict[newkey] = ddict[oldkey]
        del ddict[oldkey]
    return ddict

def renkeys(ddict, pair_list):
    for oldkey, newkey in pair_list:
        renkey(ddict, oldkey, newkey)

def take(n, items):
    return itertools.islice(items, n)

def pad_msid(msid):
    return '%05d' % int(msid)
