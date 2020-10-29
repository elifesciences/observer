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

def test_thumbnail_dimensions():
    cases = [
        # given (max, x, y) => expected (x, y)

        # no zeroes allowed. prevents errant divide-by-zero problems
        ([1, 0, 0], (1, 1)),

        # no surprises here
        ([1, 1, 1], (1, 1)),
        ([1, 2, 1], (1, 1)),
        ([1, 1, 2], (1, 1)),
        ([2, 2, 2], (2, 2)),
        ([2, 1, 2], (1, 2)),
        ([2, 2, 1], (2, 1)),
        ([800, 800, 800], (800, 800)),
        ([800, 800, 600], (800, 600)),
        ([800, 600, 800], (600, 800)),

        # images below are scaled up
        ([800, 750, 400], (800, 426)),

        # images above are scaled down
        ([800, 7500, 4000], (800, 426)),
    ]
    for given, expected in cases:
        assert expected == utils.thumbnail_dimensions(*given)
