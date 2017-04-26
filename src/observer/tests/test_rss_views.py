from observer.utils import listfiles
import re
from os.path import join
from .base import BaseCase
from django.test import Client
from django.core.urlresolvers import reverse
from observer import ingest_logic, models

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

    def test_missing_article_gives_404(self):
        url = reverse('report', kwargs={'name': 'pants-report'})
        resp = self.c.get(url)
        self.assertEqual(404, resp.status_code)

    def test_latest_articles_report_exists(self):
        url = reverse('report', kwargs={'name': 'latest-articles'})
        resp = self.c.get(url)
        self.assertEqual(200, resp.status_code)

    def test_upcoming_articles_report_exists(self):
        url = reverse('report', kwargs={'name': 'upcoming-articles'})
        resp = self.c.get(url)
        self.assertEqual(200, resp.status_code)

    def test_article_report_author_data_rss(self):
        expected_authors = 24
        msid = ingest_logic.file_upsert(join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json'))
        art = models.Article.objects.get(msid=msid)
        self.assertEqual(art.authors.count(), expected_authors)

        url = reverse('report', kwargs={'name': 'latest-articles'})
        resp = self.c.get(url)
        xml = resp.content.decode('utf-8')

        regex = r"<author.?>"
        matches = re.findall(regex, xml)
        self.assertEqual(expected_authors, len(matches))

    def test_article_report_subject_data_rss(self):
        expected_subjects = 2
        msid = ingest_logic.file_upsert(join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json'))
        art = models.Article.objects.get(msid=msid)
        self.assertEqual(art.subjects.count(), expected_subjects)

        url = reverse('report', kwargs={'name': 'latest-articles'})
        resp = self.c.get(url)
        xml = resp.content.decode('utf-8')

        regex = r"<category.?>"
        matches = re.findall(regex, xml)
        self.assertEqual(expected_subjects, len(matches))

class Two(BaseCase):
    def setUp(self):
        self.c = Client()

    def tearDown(self):
        pass

    def test_report_paginated(self):
        for path in listfiles(join(self.fixture_dir, 'ajson'), ['.json']):
            ingest_logic.file_upsert(path)
        ingest_logic.regenerate_all()
        expected_articles = 4 # 4 articles, 11 article versions
        self.assertEqual(models.Article.objects.count(), expected_articles)

        url = reverse('report', kwargs={'name': 'latest-articles'})
        resp = self.c.get(url, {'per-page': 2})

        expected_articles = 2 # 2 per page
        xml = resp.content.decode('utf-8')

        regex = r"<item>"
        matches = re.findall(regex, xml)
        self.assertEqual(len(matches), expected_articles)
