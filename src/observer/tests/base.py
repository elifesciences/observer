import json
import os
from django.test import TestCase
from io import StringIO
from django.core.management import call_command as dj_call_command

THIS_DIR = os.path.dirname(os.path.realpath(__file__))
FIXTURE_DIR = os.path.join(THIS_DIR, 'fixtures')

def call_command(*args, **kwargs):
    stdout = StringIO()
    try:
        kwargs['stdout'] = stdout
        dj_call_command(*args, **kwargs)
    except SystemExit as err:
        return err.code, stdout.getvalue()
    raise AssertionError("management commands should always throw a systemexit()")

def jsonfix(*bits):
    bits = [FIXTURE_DIR] + list(bits)
    path = os.path.join(*bits)
    return json.load(open(path, 'r'))

class BaseCase(TestCase):
    this_dir = THIS_DIR
    fixture_dir = FIXTURE_DIR

    def freshen(self, obj):
        return type(obj).objects.get(pk=obj.pk)

    def jsonfix(self, *bits):
        bits = [self.fixture_dir] + list(bits)
        path = os.path.join(*bits)
        return json.load(open(path, 'r'))
