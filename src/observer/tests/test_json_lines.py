import json
from os.path import join
from . import base
from observer import utils, ingest_logic
from django.test import Client
from django.urls import reverse

class JsonLinesResponse(base.BaseCase):
    def setUp(self):
        self.c = Client()
        for path in utils.listfiles(join(self.fixture_dir, 'ajson'), ['.json']):
            ingest_logic.file_upsert(path)
        ingest_logic.regenerate_all()

    def test_json_lines_response(self):
        url = reverse('report', kwargs={'name': 'published-research-article-index'})
        resp = self.c.get(url, {'format': 'json'})
        self.assertEqual(resp.status_code, 200)

        expected = [
            {'manuscript_id': 13964,
             'poa_published_date': '2016-05-16T00:00:00Z',
             'vor_published_date': '2016-06-15T00:00:00Z'},
            {'manuscript_id': 14850,
             'poa_published_date': None,
             'vor_published_date': '2016-07-21T00:00:00Z'},
            {'manuscript_id': 15378,
             'poa_published_date': '2016-07-29T00:00:00Z',
             'vor_published_date': '2016-08-22T16:00:29Z'},
            {'manuscript_id': 18675,
             'poa_published_date': '2016-08-23T00:00:00Z',
             'vor_published_date': '2016-09-16T10:13:54Z'},
            {'manuscript_id': 20125,
             'poa_published_date': '2016-09-08T00:00:00Z',
             'vor_published_date': None}
        ]
        data_rows = list(map(lambda row: json.loads(row.decode('utf8')), list(resp.streaming_content)))
        self.assertEqual(expected, data_rows)
