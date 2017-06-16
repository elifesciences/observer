import os
from os.path import join
import json
from .base import BaseCase, call_command
from observer import models, utils

class Cmd(BaseCase):
    def setUp(self):
        self.nom = 'load_from_fs'
        self.ajson_fixture = join(self.fixture_dir, 'ajson', 'elife-13964-v1.xml.json')
        self.num_unique_articles = 5
        self.temp_dir, self.temp_dir_cleaner = utils.tempdir()

    def tearDown(self):
        self.temp_dir_cleaner() # destroy temp dir

    def test_single_ingest_from_cli(self):
        "ensure an ingest from the cli can happen targeting a specific file"
        args = [self.nom, '--target', self.ajson_fixture]
        errcode, stdout = call_command(*args)
        self.assertEqual(errcode, 0)
        # article has been ingested
        self.assertEqual(models.Article.objects.count(), 1)

    def test_many_ingest_from_cli(self):
        "ensure an ingest from the cli can happen targeting a directory of files"
        args = [self.nom, '--target', join(self.fixture_dir, 'ajson')]
        errcode, stdout = call_command(*args)
        self.assertEqual(errcode, 0)
        # all articles have been ingested
        self.assertEqual(models.Article.objects.count(), self.num_unique_articles)

    def test_ingest_from_cli_bad_data(self):
        "ensure command fails with exit status 1 on bad data"
        self.assertEqual(models.Article.objects.count(), 0)
        args = [self.nom, '--target', '/dev/null']
        errcode, stdout = call_command(*args)
        self.assertEqual(errcode, 1)
        self.assertEqual(models.Article.objects.count(), 0)

    def test_ingest_from_cli_bad_article(self):
        self.assertEqual(models.Article.objects.count(), 0)
        data = json.load(open(self.ajson_fixture, 'r'))
        data['version'] = 2 # ingestion must start at 1 else raises StateError

        tempfile_path = join(self.temp_dir, os.path.basename(self.ajson_fixture))
        json.dump(data, open(tempfile_path, 'w'))
        self.assertTrue(os.path.exists(tempfile_path))

        args = [self.nom, '--target', tempfile_path]
        errcode, stdout = call_command(*args)
        self.assertEqual(errcode, 1)
        self.assertEqual(models.Article.objects.count(), 0)
