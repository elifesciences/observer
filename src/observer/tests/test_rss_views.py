from .base import BaseCase
from django.test import Client
from django.core.urlresolvers import reverse
'''
from unittest import skip
from os.path import join
import json
from django.test import Client, override_settings
from django.core.urlresolvers import reverse
from unittest.mock import patch, Mock
'''

class One(BaseCase):
    def setUp(self):
        self.c = Client()

    def tearDown(self):
        pass

    def test_latest_articles_rss(self):
        url = reverse('report', kwargs={'name': 'latest-articles'})
        resp = self.c.get(url)
        self.assertEqual(200, resp.status_code)
