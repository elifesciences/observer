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

        # images below are scaled up, but no more than 2x
        ([800, 200, 150], (400, 300)),

        # images above are scaled down
        ([800, 7500, 4000], (800, 426)),

        # floats are handled
        ([800, 400.5, 400], (800, 799)),
        ([800, 200.5, 150], (401, 300)),
        ([800, 150, 400.5], (299, 800)),
    ]
    for given, expected in cases:
        assert expected == utils.thumbnail_dimensions(*given)

def test_iiif_thumbnail_link():
    cases = [
        ((800, 800), "https://domain.tld/image-id.jpg/full/800,/0/default.jpg"),
        ((800, 600), "https://domain.tld/image-id.jpg/full/800,/0/default.jpg"),
        ((800, None), "https://domain.tld/image-id.jpg/full/800,/0/default.jpg"),
        ((None, 800), "https://domain.tld/image-id.jpg/full/,800/0/default.jpg"),
        ((600, 800), "https://domain.tld/image-id.jpg/full/,800/0/default.jpg"),
    ]
    uri = "https://domain.tld/image-id.jpg"
    for given, expected in cases:
        assert expected == utils.iiif_thumbnail_link(uri, *given)
