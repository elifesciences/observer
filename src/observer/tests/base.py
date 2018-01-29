import json
import os
from django.test import TestCase
from io import StringIO
from django.core.management import call_command as dj_call_command

def call_command(*args, **kwargs):
    stdout = StringIO()
    try:
        kwargs['stdout'] = stdout
        dj_call_command(*args, **kwargs)
    except SystemExit as err:
        return err.code, stdout.getvalue()
    raise AssertionError("management commands should always throw a systemexit()")

class BaseCase(TestCase):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    fixture_dir = os.path.join(this_dir, 'fixtures')

    def freshen(self, obj):
        return type(obj).objects.get(pk=obj.pk)

    def jsonfix(self, *bits):
        bits = [self.fixture_dir] + list(bits)
        path = os.path.join(*bits)
        return json.load(open(path, 'r'))
