from . import base
from os.path import join
from observer import rss, utils
import unittest

class FeedlyFeeds(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        pass

    def test_feedly_feed(self):
        "a feed built from simple data can generate a feed with Feedly fields"
        expected = open(join(base.BaseCase.fixture_dir, "feedly--dummy.rss")).read()
        report = {'title': 'feedly test feed',
                  'description': 'a dummy feed to test the additional features Feedly provides',
                  'lastBuildDate': utils.todt("2001-01-01"),
                  'link': {'href': 'https://example.org'},
                  'self-link': 'https://example.org/dummy.rss',
                  'webfeeds:accentColor': '66ff00', # bright green
                  'webfeeds:analytics': {'id': '123', 'engine': 'GoogleAnalytics'},
                  # "large rectangular image"
                  'webfeeds:cover': {'image': 'https://observer.elifesciences.org/static/large-rectangular-image.png'},

                  # "small rectangular image"
                  'webfeeds:wordmark': 'https://observer.elifesciences.org/static/small-rectangular-image.png',

                  # "small square image, similar to apple-touch-icon"
                  'webfeeds:icon': 'https://observer.elifesciences.org/static/apple-touch-icon.png',

                  'items': [{'title': 'test entry 1',
                             'description': "Cras eleifend iaculis accumsan. Ut quis eleifend magna, in porta eros. Orci varius natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Praesent sollicitudin, nibh non gravida finibus, tellus ipsum consectetur neque, a porttitor massa est porttitor elit. Ut suscipit eros urna.",
                             'link': {'href': 'https://example.org/123.html'},
                             'webfeeds:featuredImage': {'url': 'https://observer.elifesciences.org/static/reference-horizontal-M-35.png',
                                                        'height': '619',
                                                        'width': '1100',
                                                        'type': 'image/png'},
                             'id': '123',
                             'author': [{'name': 'John Everyman', 'email': 'j.everyman@example.org'}],
                             'category': [{'label': 'category 1', 'term': 'foo'},
                                          {'label': 'category 2', 'term': 'bar'}],
                             'pubDate': utils.todt('2020-09-30'),
                             'dc:dc_date': utils.ymdhms(utils.todt('2020-09-30'))},

                            {'title': 'test entry 2',
                             'description': "Morbi fringilla fringilla urna, vitae suscipit felis vehicula quis. Vestibulum vitae quam augue. Etiam ligula felis, venenatis ut consequat vel, semper non tortor. Quisque vestibulum tellus vel tortor vulputate posuere. Pellentesque imperdiet lorem sit amet libero lobortis pellentesque. Aliquam congue consectetur dolor, eget egestas eros pulvinar id.",
                             'link': {'href': 'https://example.org/456.html'},
                             'webfeeds:featuredImage': {'url': 'https://observer.elifesciences.org/static/reference-vertical-G-50.png',
                                                        'height': '877',
                                                        'width': '617',
                                                        'type': 'image/png'},
                             'id': '456',
                             'author': [{'name': 'Jane Everywoman', 'email': 'j.everywoman@example.org'}],
                             'category': [{'label': 'category 3', 'term': 'baz'},
                                          {'label': 'category 4', 'term': 'bup'}],
                             'pubDate': utils.todt('2020-09-29'),
                             'dc:dc_date': utils.ymdhms(utils.todt('2020-09-29'))}
                            ]
                  }
        context = {}
        actual = rss._format_report(report, context)
        self.assertEqual(expected, actual)
