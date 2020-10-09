from observer import utils

def test_norm_msid():
    cases = [
            (3, '3'),
            ('3', '3'),
            ('03', '3'),
            ('00000000003', '3'),
            ('0003000', '3000'),
            (3000, '3000'),
    ]
    for given, expected in cases:
        assert expected == utils.norm_msid(given)
