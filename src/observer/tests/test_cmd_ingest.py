import tempfile
import os
from os.path import join
import json
from .base import BaseCase
from io import StringIO
from django.core.management import call_command
from observer import models

class Cmd(BaseCase):
    def setUp(self):
        self.nom = 'ingest'
        self.ajson_fixture = self.ajson_list()[0]
        self.num_unique_articles = 4

    def tearDown(self):
        pass

    def call_command(self, *args, **kwargs):
        stdout = StringIO()
        try:
            kwargs['stdout'] = stdout
            call_command(*args, **kwargs)
        except SystemExit as err:
            return err.code, stdout
        self.fail("ingest script should always throw a systemexit()")

    def test_single_ingest_from_cli(self):
        "ensure an ingest from the cli can happen targeting a specific file"
        args = [self.nom, '--target', self.ajson_fixture]
        errcode, stdout = self.call_command(*args)
        self.assertEqual(errcode, 0)
        # article has been ingested
        self.assertEqual(models.Article.objects.count(), 1)

    def test_many_ingest_from_cli(self):
        "ensure an ingest from the cli can happen targeting a directory of files"
        args = [self.nom, '--target', join(self.fixture_dir, 'ajson')]
        errcode, stdout = self.call_command(*args)
        self.assertEqual(errcode, 0)
        # all articles have been ingested
        self.assertEqual(models.Article.objects.count(), self.num_unique_articles)

    def test_ingest_from_cli_bad_data(self):
        "ensure command fails with exit status 1 on bad data"
        self.assertEqual(models.Article.objects.count(), 0)
        args = [self.nom, '--target', '/dev/null']
        errcode, stdout = self.call_command(*args)
        self.assertEqual(errcode, 1)
        # article has been ingested
        self.assertEqual(models.Article.objects.count(), 0)

    def test_ingest_from_cli_bad_article(self):
        self.assertEqual(models.Article.objects.count(), 0)
        data = json.load(open(self.ajson_fixture, 'r'))
        data['article']['version'] = 2 # ingestion must start at 1 else raises StateError
        data['snippet']['version'] = 2

        # write a temporary file to pass to command
        tempdir = tempfile.mkdtemp()
        tempfile_path = join(tempdir, os.path.basename(self.ajson_fixture))
        json.dump(data, open(tempfile_path, 'w'))

        args = [self.nom, '--target', tempfile_path]
        errcode, stdout = self.call_command(*args)
        self.assertEqual(errcode, 1)
        self.assertEqual(models.Article.objects.count(), 0)
