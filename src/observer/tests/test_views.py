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
        "ensure all of the known reports can be hit with a successful response"
        known_reports = reports.known_report_idx().keys()
        for name in known_reports:
            url = reverse('report', kwargs={'name': name})
            self.assertEqual(self.c.get(url).status_code, 200, "report at %r returned non-200 response" % url)
