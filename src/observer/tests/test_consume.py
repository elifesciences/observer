from unittest import mock
from observer import consume, models

def test_consume():
    expected = {'omg': 'pants'}
    mock_request = mock.MagicMock(json=lambda: expected)
    with mock.patch('requests.get', return_value=mock_request):
        assert expected == consume.consume("whatever")

def test_content_type_from_endpoint():
    """given a request, the content-type identifier is correctly generated.
    the content-type identifier is used as an index for `models.ArticleJSON.ajson_type`"""
    cases = [
            ('/press-packages', 'press-packages-id'),
            ('/press-packages/{id}', 'press-packages-id'), # specific press package

            ('/profiles', 'profiles-id'),
            ('/profiles/{id}', 'profiles-id'),

            ('/digests', 'digests-id'),

            # exceptions to the rule
            ('/articles/{id}/versions/{version}', models.LAX_AJSON), # not actually used (yet)
            ('/metrics/article/summary', models.METRICS_SUMMARY),
    ]
    for given, expected in cases:
        actual = consume.content_type_from_endpoint(given)
        assert expected == actual
