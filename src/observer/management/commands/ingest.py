import os, sys, json
from django.core.management.base import BaseCommand
import logging
from observer import ingest_logic, models

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ingest article-json from a file or stdin'

    def add_arguments(self, parser):
        parser.add_argument('--target', required=True, action='store')

    def handle(self, *args, **options):
        self.log_context = {}

        models.Article.objects.all().delete()

        original_target = options['target']
        target = os.path.abspath(os.path.expanduser(original_target))

        fn = ingest_logic.file_upsert
        if os.path.isdir(target):
            fn = ingest_logic.bulk_file_upsert

        try:
            fn(target)
            sys.exit(0)

        except json.JSONDecodeError as err:
            LOG.error("failed to load your bad data: %s", err)

        except ingest_logic.StateError as err:
            LOG.error("failed to ingest article: %s", err)

        except ValueError as err:
            LOG.error("failed to ingest article, bad data: %s", err)

        except:
            LOG.exception("unhandled exception attempting to ingest article", extra=self.log_context)
            raise

        sys.exit(1)
