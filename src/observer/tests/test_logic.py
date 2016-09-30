import json
from os.path import join
from django.test import TestCase
from .base import BaseCase
from observer import logic, models

class Logic(BaseCase):
    def setUp(self):
        self.article_json = json.load(open(self.ajson_list()[0], 'r'))

    def test_flatten(self):
        logic.flatten_article_json(self.article_json)

    def test_upsert(self):
        self.assertEqual(models.Article.objects.count(), 0)
        logic.upsert_article_json(self.article_json, {})
        self.assertEqual(models.Article.objects.count(), 1)

    def test_bulk_upsert(self):
        res = logic.bulk_upsert(join(self.fixture_dir, 'ajson'))
        print(res)
        self.assertTrue(False)
        
