"""./manage.py load_from_fs

Development command used to load articles that have already been converted to article-json in bulk.

If the given `--target` looks like a directory, it will attempt to load any article-json files from it.

It it's a file, it will assume it's article-json and attempt to load it.

This command was more useful during initial development and while we maintained a repository of article-json files:
https://github.com/elifesciences/elife-article-json"""

import os, sys, json
from django.core.management.base import BaseCommand
import logging
from observer import ingest_logic

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ingest article-json from a file or stdin'

    def add_arguments(self, parser):
        parser.add_argument('--target', required=True, action='store')

    def handle(self, *args, **options):
        original_target = options['target']
        target = os.path.abspath(os.path.expanduser(original_target))

        fn = ingest_logic.file_upsert
        if os.path.isdir(target):
            fn = ingest_logic.bulk_file_upsert

        try:
            fn(target)

        except json.JSONDecodeError as err:
            LOG.error("failed to load, bad data: %s", err)
            sys.exit(1)

        except ingest_logic.StateError as err:
            LOG.error("failed to ingest article: %s", err)
            sys.exit(1)

        except ValueError as err:
            LOG.error("failed to ingest article, bad data: %s", err)
            sys.exit(1)

        except BaseException:
            LOG.exception("unhandled exception attempting to ingest article")
            raise

        sys.exit(0)
