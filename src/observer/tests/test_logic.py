import json
from os.path import join
from .base import BaseCase
from observer import logic, models

class Logic(BaseCase):
    def setUp(self):
        self.unique_article_count = 4
        self.article_json = self.ajson_list()[0]

    def test_flatten(self):
        article_json = json.load(open(self.article_json, 'r'))
        article_json['article']['version'] = 1 # patch fixture with missing
        logic.flatten_article_json(article_json)

    def test_upsert(self):
        self.assertEqual(models.Article.objects.count(), 0)
        logic.file_upsert(self.article_json)
        self.assertEqual(models.Article.objects.count(), 1)

    def test_bulk_upsert(self):
        self.assertEqual(models.Article.objects.count(), 0)
        logic.bulk_upsert(join(self.fixture_dir, 'ajson'))
        self.assertEqual(models.Article.objects.count(), self.unique_article_count)
