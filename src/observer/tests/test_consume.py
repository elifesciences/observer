import json
from . import base
from os.path import join
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

class Upsert(base.BaseCase):
    def setUp(self):
        pass

    def test_multiple_types_are_upserted(self):
        "different types of consumed data can be inserted/updated in models.ArticleJSON"
        cases = [
            # disabled because these two use `ingest_logic.upsert_ajson` rather than `consume.upsert`!
            # TODO: replace `ingest_logic.upsert_ajson` with `consume.upsert`
            #('article/1234', 'ajson/elife-13964-v1.xml.json'),
            #('metrics/1234', 'metrics-summary/9560.json'),
            ('profiles/1234', 'profiles/ssiyns7x.json'),
            ('press-packages/1234', 'presspackages/81d42f7d.json'),
            ('digests/1234', 'digests/59885.json'),
        ]

        for endpoint, fixture in cases:
            fixture_data = json.load(open(join(base.FIXTURE_DIR, fixture), 'r'))

            # this is all it takes to get articles and metrics to work as well
            # if endpoint == 'metrics/1234':
            #    fixture_data = fixture_data['items'][0]

            with mock.patch('observer.consume.consume', return_value=fixture_data):
                consume.single(endpoint)

        expected = 5 - 2
        self.assertEqual(expected, models.ArticleJSON.objects.count())

    def test_multiple_types_sharing_id_are_upserted(self):
        "different types of consumed data can be inserted/updated in models.ArticleJSON"
        cases = [
            # *not* disabled because I'm proving a point
            ('article/1234', 'ajson/elife-13964-v1.xml.json'),
            ('metrics/1234', 'metrics-summary/9560.json'),
            ('profiles/1234', 'profiles/ssiyns7x.json'),
            ('press-packages/1234', 'presspackages/81d42f7d.json'),
            ('digests/1234', 'digests/59885.json'),
        ]

        def insert():
            for endpoint, fixture in cases:
                fixture_data = json.load(open(join(base.FIXTURE_DIR, fixture), 'r'))
                if endpoint == 'metrics/1234':
                    fixture_data = fixture_data['items'][0]
                fixture_data['id'] = 1234

                with mock.patch('observer.consume.consume', return_value=fixture_data):
                    consume.single(endpoint)

        expected = 5

        insert()
        self.assertEqual(expected, models.ArticleJSON.objects.count())

        insert()
        self.assertEqual(expected, models.ArticleJSON.objects.count())
