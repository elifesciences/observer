from datetime import datetime, date
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

def test_ymd():
    cases = [
        (None, None),
        ("2001-12-13", "2001-12-13"),
        ("2001-12-13T23:59:59Z", "2001-12-13"),
        (datetime(2001, 12, 13, 23, 59, 59), "2001-12-13"),
        (date(2001, 12, 13), "2001-12-13")
    ]
    for given, expected in cases:
        assert expected == utils.ymd(given)
