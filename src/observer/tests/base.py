import os
from os.path import join
from django.test import TestCase
from observer.utils import lmap, lfilter

class BaseCase(TestCase):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    fixture_dir = os.path.join(this_dir, 'fixtures')

    def ajson_list(self):
        path = join(self.fixture_dir, 'ajson')
        is_ajson = lambda p: p.endswith('.xml.json')
        fullpath = lambda fname: join(path, fname)
        return lfilter(is_ajson, lmap(fullpath, os.listdir(path)))

    def freshen(self, obj):
        return type(obj).objects.get(pk=obj.pk)
