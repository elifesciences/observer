import os
from django.test import TestCase

class BaseCase(TestCase):
    this_dir = os.path.dirname(os.path.realpath(__file__))
    fixture_dir = os.path.join(this_dir, 'fixtures')

    def freshen(self, obj):
        return type(obj).objects.get(pk=obj.pk)
