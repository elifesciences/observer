import copy
from .base import BaseCase
from observer import reports
from django.test import Client
from django.core.urlresolvers import reverse

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
