#from functools import reduce
#from datetime import datetime
#from observer.utils import listfiles
#import re
from os.path import join
from .base import BaseCase
from django.test import Client
from django.core.urlresolvers import reverse
from observer import ingest_logic  # , models
from observer.utils import listfiles

class One(BaseCase):
    def setUp(self):
        self.c = Client()
        for path in listfiles(join(self.fixture_dir, 'ajson'), ['.json']):
            ingest_logic.file_upsert(path)
        ingest_logic.regenerate_all()

    def tearDown(self):
        pass

    def test_csv_report(self):
        url = reverse('report', kwargs={'name': 'published-research-article-index'})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

        for row in resp.streaming_content:
            bits = row.decode('utf8').split(',') # this particular report has no quoted comma values
            self.assertEqual(len(bits), 3)
            int(bits[0]) # first bit is an msid

