import copy
from .base import BaseCase
from observer import reports, ingest_logic, models, utils
from observer.utils import todt
from django.test import Client
from django.core.urlresolvers import reverse
from unittest import mock
from datetime import datetime, timedelta

class One(BaseCase):
    def setUp(self):
        self.c = Client()

    def test_missing_article_gives_404(self):
        url = reverse('report', kwargs={'name': 'pants-report'})
        resp = self.c.get(url)
        self.assertEqual(404, resp.status_code)

    def test_report_decorator(self):
        "test the `report` decorator modifies the function's attributes and return value correctly"
        expected_attrs = {
            'title': 'pants',
            'description': 'party'
        }

        meta = copy.deepcopy(expected_attrs) # just in case report modifies anything. it doesn't.

        @reports.report(meta)
        def foo():
            return [1, 2, 3]

        # 'meta' dictionary has been set and contains expected
        self.assertTrue(hasattr(foo, 'meta'))
        self.assertEqual(foo.meta, meta)

        # results of calling report return the meta plus an 'items' key
        expected_result = copy.deepcopy(meta)
        expected_result['items'] = [1, 2, 3]
        self.assertEqual(foo(), expected_result)

    def test_published_research_article_index_with_headers(self):
        fixtures = [
            {'msid': 123, 'current_version': 2, 'type': 'research-article',
             'datetime_poa_published': todt('2001-01-01'), 'datetime_vor_published': todt('2001-01-02')},
            
            {'msid': 456, 'current_version': 2, 'type': 'research-article',
             'datetime_poa_published': todt('2001-02-03'), 'datetime_vor_published': todt('2001-02-04')},
        ]
        for f in fixtures:
            f['doi'] = ''
            f['datetime_version_published'] = todt('1970-01-01') # obviously wrong, doesn't matter here
            utils.create_or_update(models.Article, f, ['msid'])

        report = self.c.get(reverse('report', kwargs={'name': 'published-research-article-index'}))
        report = [row.decode('utf8').strip().split(',') for row in report]

        expected = [
            ['manuscript_id', 'poa_published_date', 'vor_published_date'],
            ['123', '2001-01-01 00:00:00+00:00', '2001-01-02 00:00:00+00:00'],
            ['456', '2001-02-03 00:00:00+00:00', '2001-02-04 00:00:00+00:00']
        ]
        self.assertEqual(expected, report)

    def test_profile_counts(self):
        expected = self.jsonfix('profiles', 'many.json')
        expected['total'] = 100
        with mock.patch('observer.consume.consume', return_value=expected):
            ingest_logic.download_all_profiles()
            ingest_logic.regenerate_all_profiles()

        today = datetime.now()
        yesterday = today - timedelta(days=1)
        models.Profile.objects.filter(id="pxl5don5").update(datetime_record_created=yesterday)

        results = [(utils.ymd(x['day']), x['count']) for x in reports.profile_count()['items']]

        self.assertEqual(len(results), 2) # two groups, yesterday and today

        expected = [
            (utils.ymd(today), 99), # most recent
            (utils.ymd(yesterday), 1), # least recent
        ]
        self.assertEqual(expected, results)
