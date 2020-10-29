from os.path import join
from django.test import Client
from .base import BaseCase
from observer import reports, ingest_logic, models, utils
from django.urls import reverse
from observer.utils import listfiles, lmap
from functools import reduce

def http_dummy_params(reportfn):
    param_map = {
        'subjects': {'subject': 'cell-biology'}
    }
    kwargs = {}
    if reportfn.meta['params']:
        kwargs = utils.subdict(param_map, reportfn.meta['params'].keys())
        kwargs = reduce(utils.dict_update, kwargs.values())
    return kwargs

def dummy_params(reportfn):
    param_map = {
        'subjects': ['cell-biology']
    }
    kwargs = {}
    if reportfn.meta['params']:
        kwargs = utils.subdict(param_map, reportfn.meta['params'].keys())
    return kwargs

class Zero(BaseCase):
    def test_reports_no_data(self):
        "an unpopulated observer instance doesn't break when empty"
        self.assertEqual(models.Article.objects.count(), 0)
        for report_name, reportfn in reports.known_report_idx().items():
            report = reportfn(**dummy_params(reportfn))
            for output_format in report['serialisations']:
                context = {}
                resp = reports.format_report(report, output_format, context)
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
            report = reportfn(**dummy_params(reportfn))
            for output_format in report['serialisations']:
                context = {}
                resp = reports.format_report(report, output_format, context)
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
        "all known reports in all supported formats can be hit with a successful response"
        for report_name, reportfn in reports.known_report_idx().items():
            url = reverse('report', kwargs={'name': report_name})
            for output_format in reportfn.meta['serialisations']:
                args = {'format': output_format}
                args.update(http_dummy_params(reportfn))
                resp = self.c.get(url, args)
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

        fixtures = {
            models.LAX_AJSON: listfiles(join(self.fixture_dir, 'ajson'), ['.json']),
            models.PROFILE: [join(self.fixture_dir, 'profiles', 'ssiyns7x.json')],
            models.DIGEST: [join(self.fixture_dir, 'digests', 'many.json')],
            models.LABS_POST: [join(self.fixture_dir, 'labs-posts', 'many.json')],
            models.COMMUNITY: [join(self.fixture_dir, 'community', 'many.json')],
        }
        for content_type, path_list in fixtures.items():
            for path in path_list:
                ingest_logic.file_upsert(path, content_type, regen=False)
        ingest_logic.regenerate_all()

    def test_report_format_hint(self):
        "providing a file extension to a report name is the same as providing ?format=foo"
        for report_name, reportfn in reports.known_report_idx().items():
            url = reverse('report', kwargs={'name': report_name})
            for output_format in reportfn.meta['serialisations']:
                furl = url + ".%s" % output_format.lower() # ll /report/latest-articles.csv
                resp = self.c.get(furl, http_dummy_params(reportfn))  # , {'format': format}) # deliberate, no explicit param is provided
                self.assertEqual(resp.status_code, 200, "report at %r returned non-200 response" % furl)

                # test the content
                if output_format == reports.CSV:
                    # it's a list of strings with commas in it.
                    list(resp.streaming_content)[0].decode('utf8').split(',')[0]
                elif output_format == reports.RSS:
                    # it's an xml doc
                    prefix = "<?xml version='1.0' encoding='UTF-8'?>"
                    resp.content.decode('utf8').startswith(prefix)

    def test_report_format_param_overrides_format_hint(self):
        "the `format=` parameter wins when providing both a file extension hint and an explicit parameter"

        for report_name, reportfn in reports.known_report_idx().items():
            url = reverse('report', kwargs={'name': report_name})
            for output_format in reportfn.meta['serialisations']:
                # nothing has a .foo ext, it should be ignored in favour of the format
                furl = url + ".foo" # ll /report/latest-articles.foo
                resp1 = self.c.get(furl, http_dummy_params(reportfn))
                self.assertEqual(resp1.status_code, 400) # bad request

                args = {'format': output_format}
                args.update(http_dummy_params(reportfn))
                resp2 = self.c.get(furl, args) # good request, provide an explicit format param
                self.assertEqual(resp2.status_code, 200, "report at %r returned non-200 response" % url)

                # test the content
                if output_format == reports.CSV:
                    # it's a list of strings with commas in it.
                    list(resp2.streaming_content)[0].decode('utf8').split(',')[0]
                elif output_format == reports.RSS:
                    # it's an xml doc
                    prefix = "<?xml version='1.0' encoding='UTF-8'?>"
                    resp2.content.decode('utf8').startswith(prefix)

class Five(BaseCase):
    def setUp(self):
        self.c = Client()

    def test_ping(self):
        resp = self.c.get(reverse('ping'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['content-type'], 'text/plain; charset=UTF-8')
        self.assertEqual(resp['cache-control'], 'must-revalidate, no-cache, no-store, private')
        self.assertEqual(resp.content.decode('utf-8'), 'pong')
