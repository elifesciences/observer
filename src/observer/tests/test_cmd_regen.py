from os.path import join
from .base import BaseCase, call_command
from observer import models, ingest_logic

class Cmd(BaseCase):
    def setUp(self):
        self.nom = 'regen'

    def tearDown(self):
        pass

    def test_regen_no_articles(self):
        args = [self.nom]
        errcode, stdout = call_command(*args)
        self.assertEqual(errcode, 0)

    def test_regen_some_articles(self):
        self.article_json = join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json')

        # load the ArticleJSON in
        ingest_logic.file_upsert(self.article_json, regen=False)

        # ensure no articles exist yet
        self.assertEqual(models.Article.objects.count(), 0)

        args = [self.nom]
        errcode, stdout = call_command(*args)

        self.assertEqual(errcode, 0)

        # article has been ingested
        self.assertEqual(models.Article.objects.count(), 1)
