from . import base
from observer import utils

class One(base.BaseCase):
    def setUp(self):
        pass

    def test_norm_msid(self):
        cases = [
            (3, '3'),
            ('3', '3'),
            ('03', '3'),
            ('00000000003', '3'),
            ('0003000', '3000'),
            (3000, '3000'),
        ]
        for given, expected in cases:
            self.assertEqual(expected, utils.norm_msid(given))
