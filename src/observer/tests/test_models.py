from .base import BaseCase
from observer import models
from observer.utils import first, create_or_update

class One(BaseCase):
    def setUp(self):
        data = [
            ('article', models.Article, {'msid': 666, 'journal_name': 'eLife', 'datetime_version_published': '2001-01-01'}, ['msid']),
            ('author', models.Author, {'type': 'person', 'name': "John Jameson", "country": "uk"}, ['id']),
            ('subject', models.Subject, {'name': 'pants', 'label': 'Pants'}, ['id']),
            ('ajson', models.ArticleJSON, {'msid': 666, 'version': 1, 'ajson': 'pantsparty', 'ajson_type': models.LAX_AJSON}, ['id']),
            ('profile', models.Profile, {'id': 'foo', 'name': 'Bar', 'orcid': "0000-0001-5910-5972"}, ['id']),
        ]
        for row in data:
            setattr(self, row[0], first(create_or_update(*row[1:])))

    def tearDown(self):
        pass

    def test_models_printable(self):
        "all models have a str-friendly version"
        cases = [
            # obj, repr(), str()
            (self.article, '<Article "00666">', '00666'),
            (self.author, '<Author "John Jameson">', 'John Jameson'),
            (self.subject, '<Subject "pants">', 'Pants'),
            (self.ajson, '<ArticleJSON "00666 v1">', "00666 v1"),
            (self.profile, '<Profile "0000-0001-5910-5972">', "0000-0001-5910-5972"),
        ]
        for obj, expected_repr, expected_str in cases:
            self.assertEqual(repr(obj), expected_repr)
            self.assertEqual(str(obj), expected_str)
