from unittest import mock
from observer import consume
from . import base

class One(base.BaseCase):

    def test_consume(self):
        expected = {'omg': 'pants'}
        mock_request = mock.MagicMock(json=lambda: expected)
        with mock.patch('requests.get', return_value=mock_request):
            self.assertEqual(consume.consume("whatever"), expected)
