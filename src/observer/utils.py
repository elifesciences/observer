from functools import partial
from rfc3339 import rfc3339
import os
from os.path import join
import copy
from dateutil import parser
from datetime import datetime
import pytz
import itertools
import logging
import tempfile
import shutil
from math import ceil

LOG = logging.getLogger(__name__)

def nth(x, n):
    try:
        return x[n]
    except IndexError:
        return None

first = partial(nth, n=0)
second = partial(nth, n=1)
third = partial(nth, n=2)

def ensure(assertion, msg, *args):
    """intended as a convenient replacement for `assert` statements that
    get compiled away with -O flags"""
    if not assertion:
        raise AssertionError(msg % args)

def delall(ddict, lst):
    "mutator. "
    def delkey(key):
        try:
            del ddict[key]
            return True
        except KeyError:
            return False
    return list(zip(lst, lmap(delkey, lst)))

def listfiles(path, ext_list=None):
    "returns a list of absolute paths for given dir"
    path_list = map(lambda fname: os.path.abspath(join(path, fname)), os.listdir(path))
    if ext_list:
        path_list = filter(lambda path: os.path.splitext(path)[1] in ext_list, path_list)
    return sorted(filter(os.path.isfile, path_list))

def update(d1, d2):
    d1.update(d2)
    return d1

def isint(v):
    try:
        int(v)
        return True
    except (ValueError, TypeError):
        return False

lmap = lambda func, *iterable: list(map(func, *iterable))
lfilter = lambda func, *iterable: list(filter(func, *iterable))

def val_map(fn, d):
    return {k: fn(v) for k, v in d.items()}

def key_map(fn, d):
    return {fn(k): v for k, v in d.items()}

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

def ymdhms(dt):
    "returns an rfc3339 representation of a datetime object"
    if dt:
        dt = todt(dt) # convert to utc, etc
        return rfc3339(dt, utc=True)

def ymd(dt):
    if dt:
        dt = todt(dt)
        return dt.strftime("%Y-%m-%d")

def subdict(dt, ks):
    "returns a copy of the given dictionary `dt` with only the keys `ks` included"
    return {k: v for k, v in dt.items() if k in ks}

# http://stackoverflow.com/questions/434287/what-is-the-most-pythonic-way-to-iterate-over-a-list-in-chunks
def partition(seq, size):
    res = []
    for el in seq:
        res.append(el)
        if len(res) == size:
            yield res
            res = []
    if res:
        yield res

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


def to_dict(instance, descend_into_mn_fields=False):
    from django.db.models.fields.related import ManyToManyField
    opts = instance._meta
    data = {}
    for f in opts.concrete_fields + opts.many_to_many:
        if isinstance(f, ManyToManyField) and descend_into_mn_fields:
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

EXCLUDE_ME = 0xDEADBEEF

def create_or_update(Model, orig_data, key_list=None, create=True, update=True, commit=True, **overrides):
    inst = None
    created = updated = False
    data = {}
    data.update(orig_data)
    data.update(overrides)
    key_list = key_list or data.keys()
    try:
        # try and find an entry of Model using the key fields in the given data
        inst = Model.objects.get(**subdict(data, key_list))
        # object exists, otherwise DoesNotExist would have been raised
        if update:
            [setattr(inst, key, val) for key, val in data.items() if val != EXCLUDE_ME]
            updated = True
    except Model.DoesNotExist:
        if create:
            #inst = Model(**data)
            # shift this exclude me handling to et3
            inst = Model(**{k: v for k, v in data.items() if v != EXCLUDE_ME})
            created = True

    if (updated or created) and commit:
        inst.save()

    # it is possible to neither create nor update.
    # in this case if the model cannot be found then None is returned: (None, False, False)
    return (inst, created, updated)

def tempdir():
    # usage: tempdir, killer = tempdir(); killer()
    name = tempfile.mkdtemp()
    return (name, lambda: shutil.rmtree(name))

# TODO: shift this to elife-metrics
def byte_length(i):
    return ceil(i.bit_length() / 8.0)
