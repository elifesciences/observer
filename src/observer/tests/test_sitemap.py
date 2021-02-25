from observer import sitemap, models
import unittest

class SiteMap(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        pass

    def test_feedly_feed(self):
        "a feed built from simple data can generate a feed with Feedly fields"
        report = {'title': 'test sitemap',
                  'description': "a test sitemap that doesn't touch the database",
                  'items': [
                      # dictionaries
                      # timezones are normalised to UTC.
                      {"url": "https://elifesciences.org/articles/61639", "last-modified": "2021-02-08T10:55:27-05:00"},

                      # tuples
                      # data is passed through, timezones are *not* normalised to UTC.
                      ("https://elifesciences.org/articles/61082", "2021-02-09T10:07:34-05:00"),

                      # models.Article objects
                      # the date of the most recent version is used.
                      # short msids are padded
                      models.Article(**{
                          'journal_name': 'eLife',
                          'msid': 123,
                          'type': 'research-article',
                          'datetime_version_published': '2001-01-01T01:02:03Z',
                      }),

                      # models.Content objects
                      # timezones are normalised to UTC.
                      # `datetime_updated` is preferred over `datetime_published`.
                      models.Content(**{
                          'id': '123456',
                          'title': "doesn't matter",
                          'content_type': models.INTERVIEW,
                          'datetime_published': "2021-02-09T07:30:07-05:00",
                          'datetime_updated': "2021-02-10T07:30:07-05:00"
                      }),
                      models.Content(**{
                          'id': '789012',
                          'title': "still doesn't matter",
                          'content_type': models.COLLECTION,
                          'datetime_published': "2021-02-09T07:30:07-05:00"
                      }),
                      models.Content(**{
                          'id': '12345',
                          'title': "doesn't matter",
                          'content_type': models.BLOG_ARTICLE,
                          'datetime_published': "2021-02-09T07:30:07Z"
                      }),
                      models.Content(**{
                          'id': '23456',
                          'title': "doesn't matter",
                          "content_type": models.FEATURE,
                          "datetime_published": "2021-02-09T07:30:07Z"
                      }),
                      models.Content(**{
                          'id': '23456',
                          'title': "doesn't matter",
                          "content_type": models.EDITORIAL,
                          "datetime_published": "2021-02-09T07:30:07Z"
                      }),
                      models.Content(**{
                          'id': '23456',
                          'title': "doesn't matter",
                          "content_type": models.INSIGHT,
                          "datetime_published": "2021-02-09T07:30:07Z"
                      }),
                      models.Content(**{
                          'id': '23456',
                          'title': "doesn't matter",
                          "content_type": models.DIGEST,
                          "datetime_published": "2021-02-09T07:30:07Z"
                      }),
                      models.Content(**{
                          'id': '23456',
                          'title': "doesn't matter",
                          "content_type": models.LABS_POST,
                          "datetime_published": "2021-02-09T07:30:07Z"
                      }),
                      models.Content(**{
                          'id': '23456',
                          'title': "doesn't matter",
                          "content_type": models.PODCAST,
                          "datetime_published": "2021-02-09T07:30:07Z"
                      }),

                      # models.PressPackage
                      # prefers `updated` over `published`
                      models.PressPackage(**{
                          'id': '2adbe814',
                          'title': "doesn't matter",
                          'published': "2021-02-02T01:02:03Z",
                          "updated": "2021-02-03T02:03:04Z"
                      }),
                  ]}
        context = {}
        expected = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">
  <url>
    <loc>https://elifesciences.org/articles/61639</loc>
    <lastmod>2021-02-08T15:55:27Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/articles/61082</loc>
    <lastmod>2021-02-09T10:07:34-05:00</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/articles/00123</loc>
    <lastmod>2001-01-01T01:02:03Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/interviews/123456</loc>
    <lastmod>2021-02-10T12:30:07Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/collections/789012</loc>
    <lastmod>2021-02-09T12:30:07Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/inside-elife/12345</loc>
    <lastmod>2021-02-09T07:30:07Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/articles/23456</loc>
    <lastmod>2021-02-09T07:30:07Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/articles/23456</loc>
    <lastmod>2021-02-09T07:30:07Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/articles/23456</loc>
    <lastmod>2021-02-09T07:30:07Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/digests/23456</loc>
    <lastmod>2021-02-09T07:30:07Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/labs/23456</loc>
    <lastmod>2021-02-09T07:30:07Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/podcast/episode23456</loc>
    <lastmod>2021-02-09T07:30:07Z</lastmod>
  </url>
  <url>
    <loc>https://elifesciences.org/for-the-press/2adbe814</loc>
    <lastmod>2021-02-03T02:03:04Z</lastmod>
  </url>
</urlset>"""
        report = sitemap._format_report(report, context)
        actual = sitemap.realise_as_string(report)
        self.assertEqual(expected, actual)
