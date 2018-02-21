import copy
from .base import BaseCase
from observer import reports, ingest_logic, models, utils
from django.test import Client
from django.core.urlresolvers import reverse
from django.utils import timezone
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

    def test_profile_counts(self):
        #expected = self.jsonfix('profiles', 'many.json')
        #expected['total'] = 100
        #with mock.patch('observer.consume.consume', return_value=expected):
        #    ingest_logic.download_all_profiles()
        #    ingest_logic.regenerate_all_profiles()

        # create a Profile object once a day for N days
        offset = 7
        next_day = startday = timezone.now() - timedelta(days=offset)
        expected = []
        for day in range(1, offset + 1):
            pid = 'abc%s' % day
            obj, _, _ = utils.create_or_update(models.Profile, {'id': pid, 'datetime_record_created': next_day}, update=False)

            expected.append((utils.ymd(next_day), day))
            
            # increment prev day
            next_day = next_day + timedelta(days=1)

        # ll: [('2018-02-20', 7), ('2018-02-19', 6), ('2018-02-18', 5), ('2018-02-17', 4), ('2018-02-16', 3), ('2018-02-15', 2), ('2018-02-14', 1)]
        expected = expected[::-1]

        print(reports.profile_count()['items'])

        from django.db import connection
        print('----------')
        print(connection.queries)

        self.fail()
        
        actual = [(utils.ymd(x['day']), x['count']) for x in reports.profile_count()['items']]
        
        self.assertEqual(offset, len(actual))
        self.assertEqual(expected, actual)
