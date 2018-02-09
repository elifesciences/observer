from .base import BaseCase
from observer import models
from observer.utils import first, create_or_update

class One(BaseCase):
    def setUp(self):
        data = {
            'msid': 666,
            'journal_name': 'eLife',
            'datetime_version_published': '2001-01-01'
        }
        self.article = first(create_or_update(models.Article, data, ['msid']))

        data = {'type': 'person', 'name': "John Jameson", "country": "uk"}
        self.author = first(create_or_update(models.Author, data, ['id']))

        data = {'name': 'pants', 'label': 'Pants'}
        self.subject = first(create_or_update(models.Subject, data, ['id']))

        data = {'msid': 666, 'version': 1, 'ajson': 'pantsparty'}
        self.ajson = first(create_or_update(models.ArticleJSON, data, ['id']))

        #data = {'total': 12345}
        #self.profile_count = first(create_or_update(models.ProfileCount, data, ['id']))

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
            #(self.profile_count, '<ProfileCount "12345">', "12345"),
        ]
        for obj, expected_repr, expected_str in cases:
            self.assertEqual(repr(obj), expected_repr)
            self.assertEqual(str(obj), expected_str)
