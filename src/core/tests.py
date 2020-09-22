from django.test import TestCase, Client
from core.middleware import MAX_AGE, MAX_STALE

class DownstreamCaching(TestCase):
    def setUp(self):
        self.c = Client()
        self.url = '/' # we could hit more urls but it's applied application-wide

    def tearDown(self):
        pass

    def test_cache_headers_in_response(self):
        expected_headers = [
            'vary', # redundant
            'cache-control'
        ]
        resp = self.c.get(self.url)
        for header in expected_headers:
            self.assertTrue(resp.has_header(header), "header %r not found in response" % header)

    def test_cache_header_values(self):
        expected_headers = [
            ('vary', ['Accept']),
            ('cache-control', ['max-age=%s' % MAX_AGE, 'public', 'stale-if-error=%s' % MAX_STALE, 'stale-while-revalidate=%s' % MAX_AGE])
        ]
        resp = self.c.get(self.url)
        for header, expected in expected_headers:
            # dirty parsing to guarantee ordered values
            self.assertEqual(sorted(resp[header].split(', ')), expected)

    def test_cache_headers_not_in_response(self):
        cases = [
            'expires',
            'last-modified',
            'prama' # HTTP/1.0
        ]
        resp = self.c.get(self.url)
        for header in cases:
            self.assertFalse(resp.has_header(header), "header %r present in response" % header)
