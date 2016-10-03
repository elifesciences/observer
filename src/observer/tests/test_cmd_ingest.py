import tempfile
import os
import json
from .base import BaseCase
from io import StringIO
from django.core.management import call_command
from observer import models

class Cmd(BaseCase):
    def setUp(self):
        self.nom = 'ingest'
        self.ajson_fixture = self.ajson_list()[0]

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
    
    def test_ingest_from_cli(self):
        "ensure an ingest from the cli can happen"
        args = [self.nom, self.ajson_fixture]
        errcode, stdout = self.call_command(*args)
        self.assertEqual(errcode, 0)
        # article has been ingested
        self.assertEqual(models.Article.objects.count(), 1)

    def test_ingest_from_cli_bad_data(self):
        "ensure command fails with exit status 1 on bad data"
        args = [self.nom, '/dev/null']
        errcode, stdout = self.call_command(*args)
        self.assertEqual(errcode, 1)
        # article has been ingested
        self.assertEqual(models.Article.objects.count(), 0)

    def test_ingest_from_cli_bad_article(self):
        data = json.load(open(self.ajson_fixture, 'r'))
        data['article']['version'] = 2 # ingestion must start at 1 else raises StateError

        # write a temporary file to pass to command
        tempdir = tempfile.mkdtemp()
        tempfile_path = os.path.join(tempdir, os.path.basename(self.ajson_fixture))
        json.dump(data, open(tempfile_path, 'w'))
        
        args = [self.nom, tempfile_path]
        errcode, stdout = self.call_command(*args)
        self.assertEqual(errcode, 1)
        self.assertEqual(models.Article.objects.count(), 0)
