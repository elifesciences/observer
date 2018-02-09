from unittest import mock
from observer import consume, models
from . import base

class One(base.BaseCase):

    def test_consume(self):
        expected = {'omg': 'pants'}
        mock_request = mock.MagicMock(json=lambda: expected)
        with mock.patch('requests.get', return_value=mock_request):
            self.assertEqual(consume.consume("whatever"), expected)

    def test_content_type_from_endpoint(self):
        # more of a sanity check
        cases = [
            ('/press-packages', 'press-packages-id'),
            ('/press-packages/{id}', 'press-packages-id'), # specific press package

            ('/profiles', 'profiles-id'),
            ('/profiles/{id}', 'profiles-id'),

            # exceptions
            ('/articles/{id}/versions/{version}', models.LAX_AJSON), # not actually used (yet)
            ('/metrics/article/summary', models.METRICS_SUMMARY),
        ]
        for given, expected in cases:
            self.assertEqual(consume.content_type_from_endpoint(given), expected, given)
