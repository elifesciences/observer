from django.test import Client
from .base import BaseCase
from observer import reports
from django.core.urlresolvers import reverse

class One(BaseCase):
    def setUp(self):
        self.c = Client()

    def test_landing_page(self):
        resp = self.c.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_reports(self):
        "all known reports can be hit with a successful response"
        known_reports = reports.known_report_idx().keys()
        for name in known_reports:
            url = reverse('report', kwargs={'name': name})
            resp = self.c.get(url)
            self.assertEqual(resp.status_code, 200, "report at %r returned non-200 response" % url)

    def test_report_format_hint(self):
        "providing a file extension to a report name is the same as providing ?format=foo"

        # default serialization for this particular report is RSS
        self.assertEqual(reports.latest_articles.meta[reports.SERIALISATIONS][0], reports.RSS)
        
        # and here we hint we're after .json
        url = reverse('report', kwargs={'name': 'latest-articles'})
        url += ".json"
        resp = self.c.get(url)
        # the hint is understood
        self.assertEqual(resp.status_code, 200)

    def test_report_format_param_overrides_format_hint(self):
        "the format parameter wins when providing both a file extension format hint and a format param"
        pass
