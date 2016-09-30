import os
from os.path import join
from django.test import TestCase
from observer import utils

class BaseCase(TestCase):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    fixture_dir = os.path.join(this_dir, 'fixtures')

    def ajson_list(self):
        path = join(self.fixture_dir, 'ajson')
        return utils.gmap(lambda fname: join(path, fname), os.listdir(path))
    
    def freshen(self, obj):
        return type(obj).objects.get(pk=obj.pk)
