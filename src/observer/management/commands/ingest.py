import os, sys,json
from django.core.management.base import BaseCommand
import logging
from observer import logic

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ingest article-json from a file or stdin'

    def add_arguments(self, parser):
        parser.add_argument('--target', action='store')

    def handle(self, *args, **options):
        self.log_context = {}
        
        original_target = options['target']
        target = os.path.abspath(os.path.expanduser(original_target))

        fn = logic.file_upsert
        if os.path.isdir(target):
            fn = logic.bulk_upsert

        try:
            fn(target)
        except json.JSONDecodeError as err:
            LOG.error("failed to load your bad data: %s", err)
            sys.exit(1)
                
        except logic.StateError as err:
            LOG.error("failed to ingest article: %s", err)
            sys.exit(1)

        except:
            LOG.exception("unhandled exception attempting to ingest article", extra=self.log_context)
            raise

        sys.exit(0)
