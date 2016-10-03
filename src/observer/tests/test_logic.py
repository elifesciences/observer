import json
from os.path import join
from .base import BaseCase
from observer import logic, models

class Logic(BaseCase):
    def setUp(self):
        self.unique_article_count = 4
        self.article_json = self.ajson_list()[0]

    def test_flatten(self):
        "a basic transformation of the data is possible without errors"
        article_json = json.load(open(self.article_json, 'r'))
        article_json['article']['version'] = 1 # patch fixture with missing
        logic.flatten_article_json(article_json)

    def test_upsert(self):
        "a basic upsert is possible"
        self.assertEqual(models.Article.objects.count(), 0)
        logic.file_upsert(self.article_json)
        self.assertEqual(models.Article.objects.count(), 1)

    def test_bulk_upsert(self):
        "we can create/update a sample of our articles across multiple versions"
        self.assertEqual(models.Article.objects.count(), 0)
        logic.bulk_upsert(join(self.fixture_dir, 'ajson'))
        self.assertEqual(models.Article.objects.count(), self.unique_article_count)

    def test_num_versions(self):
        "ensure our version calculations are correct"
        logic.bulk_upsert(join(self.fixture_dir, 'ajson'))
        expected_versions = {
            13964: (3, 2, 1),
            14850: (1, 0, 1),
            15378: (3, 1, 2),
            18675: (4, 3, 1),
        }
        for msid, vers in expected_versions.items():
            try:
                expected_version, expected_poa, expected_vor = vers
                art = models.Article.objects.get(msid=msid)
                self.assertEqual(art.current_version, expected_version)
                self.assertEqual(art.num_poa_versions, expected_poa)
                self.assertEqual(art.num_vor_versions, expected_vor)
                self.assertEqual(art.status, models.VOR)
            except AssertionError as err:
                print('failed on',msid,'with vers',vers)
                raise err
