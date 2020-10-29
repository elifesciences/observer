from .base import BaseCase
from observer import models
from observer.utils import first, create_or_update

class One(BaseCase):
    def setUp(self):
        data = [
            ('article', models.Article, {'msid': 666, 'journal_name': 'eLife', 'datetime_version_published': '2001-01-01T00:00:00Z'}, ['msid']),
            ('author', models.Author, {'type': 'person', 'name': "John Jameson", "country": "uk"}, ['id']),
            ('subject', models.Subject, {'name': 'pants', 'label': 'Pants'}, ['id']),
            ('ajson', models.RawJSON, {'msid': 666, 'version': 1, 'json': 'pantsparty', 'json_type': models.LAX_AJSON}, ['id']),
            ('ajson2', models.RawJSON, {'msid': 667, 'version': None, 'json': 'pantsparty', 'json_type': models.METRICS_SUMMARY}, ['id']),
            #('profile', models.Profile, {'id': 'foo', 'name': 'Bar', 'orcid': "0000-0001-5910-5972"}, ['id']),
            ('profile', models.Profile, {'id': 'foo'}, ['id']),
        ]
        for row in data:
            obj = first(create_or_update(*row[1:]))
            setattr(self, row[0], self.freshen(obj))

    def tearDown(self):
        pass

    def test_models_printable(self):
        "all models have a str-friendly version"
        cases = [
            # obj, repr(), str()
            (self.article, '<Article "00666">', '00666'),
            (self.author, '<Author "John Jameson">', 'John Jameson'),
            (self.subject, '<Subject "pants">', 'Pants'),
            (self.ajson, "<RawJSON 'lax-ajson' 666v1>", "666"),
            (self.ajson2, "<RawJSON 'elife-metrics-summary' 667>", "667"),
            #(self.profile, '<Profile "0000-0001-5910-5972">', "0000-0001-5910-5972"),
            (self.profile, '<Profile "foo">', "foo"),
        ]
        for obj, expected_repr, expected_str in cases:
            self.assertEqual(repr(obj), expected_repr)
            self.assertEqual(str(obj), expected_str)
