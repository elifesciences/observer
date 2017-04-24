import sys, json
from django.core.management.base import BaseCommand
import logging
from observer import logic, ingest_logic
from observer.utils import lmap

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'regenerates Article data from database'

    def add_arguments(self, parser):
        #parser.add_argument('--msid', required=True, action='store')
        pass

    def handle(self, *args, **options):
        try:
            ingest_logic.regenerate_many(logic.known_articles())

        except json.JSONDecodeError as err:
            LOG.error("failed to load your bad data: %s", err)
            sys.exit(1)

        except ingest_logic.StateError as err:
            LOG.error("failed to ingest article: %s", err)
            sys.exit(1)

        except ValueError as err:
            LOG.error("failed to ingest article, bad data: %s", err)
            sys.exit(1)

        except:
            LOG.exception("unhandled exception attempting to ingest article")
            raise

        sys.exit(0)
