#from functools import reduce
#from datetime import datetime
#from observer.utils import listfiles
#import re
from os.path import join
from .base import BaseCase
from django.test import Client
from django.core.urlresolvers import reverse
from observer import ingest_logic, csv, reports
from observer.utils import listfiles

#
# todo: consider removing this whole file. it's pretty much covered now in test_views.py
#

class Int(BaseCase):
    def setUp(self):
        for path in listfiles(join(self.fixture_dir, 'ajson'), ['.json']):
            ingest_logic.file_upsert(path)
        ingest_logic.regenerate_all()

    def test_a_csv_report(self):
        "a report that is known to support csv rendering can do so outside of http request/response"
        report, context = reports.published_research_article_index(), {}
        # result is actually a StreamingHttpResponse, but can be traversed like an iterator
        result = csv.format_report(report, context)
        for row in result:
            bits = row.decode('utf8').split(',')
            self.assertEqual(len(bits), 3)
            int(bits[0])

class Ext(BaseCase):
    def setUp(self):
        self.c = Client()
        for path in listfiles(join(self.fixture_dir, 'ajson'), ['.json']):
            ingest_logic.file_upsert(path)
        ingest_logic.regenerate_all()

    def tearDown(self):
        pass

    def test_csv_report(self):
        "a report that is known to support csv rendering can do so within a http request/response"
        url = reverse('report', kwargs={'name': 'published-research-article-index'})
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)

        for row in resp.streaming_content:
            bits = row.decode('utf8').split(',') # this particular report has no quoted comma values
            self.assertEqual(len(bits), 3)
            int(bits[0]) # first bit is an msid
