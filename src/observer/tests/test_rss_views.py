from datetime import datetime
from observer.utils import listfiles
import re
from os.path import join
from .base import BaseCase
from django.test import Client
from django.core.urlresolvers import reverse
from observer import ingest_logic, models
from observer.utils import lmap

class One(BaseCase):
    def setUp(self):
        self.c = Client()

    def tearDown(self):
        pass

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
        for path in listfiles(join(self.fixture_dir, 'ajson'), ['.json']):
            ingest_logic.file_upsert(path, regen=False)
        ingest_logic.regenerate_all()

    def tearDown(self):
        pass

    def test_report_paginated(self):
        expected_articles = 5 # 5 articles, 12 article versions
        self.assertEqual(models.Article.objects.count(), expected_articles)

        url = reverse('report', kwargs={'name': 'latest-articles'})
        resp = self.c.get(url, {'per-page': 2})

        expected_articles = 2 # 2 per page
        xml = resp.content.decode('utf-8')

        regex = r"<item>"
        matches = re.findall(regex, xml)
        self.assertEqual(len(matches), expected_articles)

    def test_report_ordered(self):
        "ensure report is ordered correctly"
        url = reverse('report', kwargs={'name': 'latest-articles'})
        resp = self.c.get(url, {'order': 'DESC'})
        self.assertEqual(resp.status_code, 200)
        xml = resp.content.decode('utf-8')

        regex = r"<dc:date>(.+)</dc:date>"
        actual = lmap(lambda dt: datetime.strptime(dt[:10], "%Y-%m-%d"), re.findall(regex, xml))

        expected = [
            datetime(2016, 9, 8, 0, 0),
            datetime(2016, 8, 23, 0, 0),
            datetime(2016, 7, 29, 0, 0),
            datetime(2016, 7, 21, 0, 0),
            datetime(2016, 5, 16, 0, 0)
        ]

        self.assertEqual(actual, expected)

    def test_report_ordered_reverse(self):
        "ensure report is ordered correctly. reports are ordered by original date published"
        url = reverse('report', kwargs={'name': 'latest-articles'})
        resp = self.c.get(url, {'order': 'ASC'})
        xml = resp.content.decode('utf-8')

        regex = r"<dc:date>(.+)</dc:date>"
        actual = lmap(lambda dt: datetime.strptime(dt[:10], "%Y-%m-%d"), re.findall(regex, xml))

        expected = [
            datetime(2016, 5, 16, 0, 0),
            datetime(2016, 7, 21, 0, 0),
            datetime(2016, 7, 29, 0, 0),
            datetime(2016, 8, 23, 0, 0),
            datetime(2016, 9, 8, 0, 0)
        ]
        self.assertEqual(actual, expected)

    def test_report_keeps_query_count_low(self):
        # worse case here is 12 without prefetching
        magic_num = 4 # after django fanciness
        with self.assertNumQueries(magic_num):
            self.c.get(reverse('report', kwargs={'name': 'latest-articles'}))

        # worse case is also 4 without prefetching
        magic_num = 4
        with self.assertNumQueries(magic_num):
            self.c.get(reverse('report', kwargs={'name': 'upcoming-articles'}))

        # with a simple csv report that doesn't descend into many-to-many fields, we can whittle a
        # request down to just 3 requests
        paginate = 1
        csv_peek = 1
        csv_generation = 1
        num = paginate + csv_peek + csv_generation
        with self.assertNumQueries(num):
            self.c.get(reverse('report', kwargs={'name': 'latest-articles'}), {'format': 'csv'})
