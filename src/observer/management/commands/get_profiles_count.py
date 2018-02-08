import sys, json
from django.core.management.base import BaseCommand
import logging
from observer import ingest_logic

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'regenerates Article data from database'

    def handle(self, *args, **options):
        try:
            ingest_logic.download_profiles_count()
        except json.JSONDecodeError as err:
            LOG.error("failed to load your bad data: %s", err)
            sys.exit(1)

        except:
            LOG.exception("unhandled exception attempting to get profiles count")
            raise

        sys.exit(0)
