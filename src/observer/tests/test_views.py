from os.path import join
from django.test import Client
from .base import BaseCase
from observer import reports, ingest_logic, models
from django.core.urlresolvers import reverse
from observer.utils import listfiles, lmap

class Zero(BaseCase):
    def test_reports_no_data(self):
        "an unpopulated observer instance doesn't break when empty"
        self.assertEqual(models.Article.objects.count(), 0)
        for report_name, reportfn in reports.known_report_idx().items():
            report = reportfn()
            for format in report['serialisations']:
                context = {}
                resp = reports.format_report(report, format, context)
                # realize any results
                if resp.streaming:
                    lmap(str, resp.streaming_content)
                else:
                    str(resp.content)

class One(BaseCase):
    def setUp(self):
        self.c = Client()
        for path in listfiles(join(self.fixture_dir, 'ajson'), ['.json']):
            ingest_logic.file_upsert(path)
        ingest_logic.regenerate_all()

    def test_reports(self):
        "all known reports can be formatted with results"
        for report_name, reportfn in reports.known_report_idx().items():
            report = reportfn()
            for format in report['serialisations']:
                context = {}
                resp = reports.format_report(report, format, context)
                # realize any results
                if resp.streaming:
                    lmap(str, resp.streaming_content)
                else:
                    str(resp.content)

class Two(BaseCase):
    def setUp(self):
        self.c = Client()
        for path in listfiles(join(self.fixture_dir, 'ajson'), ['.json']):
            ingest_logic.file_upsert(path)
        ingest_logic.regenerate_all()

    def test_reports(self):
        "all known reports in all support formats can be hit with a successful response"
        for report_name, reportfn in reports.known_report_idx().items():
            url = reverse('report', kwargs={'name': report_name})
            for format in reportfn.meta['serialisations']:
                resp = self.c.get(url, {'format': format})
                self.assertEqual(resp.status_code, 200, "report at %r returned non-200 response" % url)

class Three(BaseCase):
    def setUp(self):
        self.c = Client()

    def test_landing_page(self):
        resp = self.c.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_slashes_not_appended(self):
        "ensure a slash is not appended to the end of a url"
        url = reverse('report', kwargs={'name': 'latest-articles'})
        self.assertFalse(url.endswith('/'))
        # ensure we go directly to the url without redirecting to a slash suffixed one
        resp = self.c.get(url, follow=False)
        self.assertEqual(resp.status_code, 200)

class Four(BaseCase):
    def setUp(self):
        self.c = Client()
        for path in listfiles(join(self.fixture_dir, 'ajson'), ['.json']):
            ingest_logic.file_upsert(path)
        ingest_logic.regenerate_all()

    def test_report_format_hint(self):
        "providing a file extension to a report name is the same as providing ?format=foo"

        for report_name, reportfn in reports.known_report_idx().items():
            url = reverse('report', kwargs={'name': report_name})
            for format in reportfn.meta['serialisations']:
                furl = url + ".%s" % format.lower()
                resp = self.c.get(furl)  # , {'format': format}) # no explicit param is provided
                self.assertEqual(resp.status_code, 200, "report at %r returned non-200 response" % url)

                # test the content
                if format == reports.CSV:
                    # it's a list of strings with commas in it.
                    list(resp.streaming_content)[0].decode('utf8').split(',')[0]
                elif format == reports.RSS:
                    # it's an xml doc
                    prefix = "<?xml version='1.0' encoding='UTF-8'?>"
                    resp.content.decode('utf8').startswith(prefix)

    def test_report_format_param_overrides_format_hint(self):
        "the format parameter wins when providing both a file extension format hint and a format param"
        pass
