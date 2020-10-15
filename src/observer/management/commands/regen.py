import sys, json
from django.core.management.base import BaseCommand
import logging
from observer import ingest_logic

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "regenerates Articles, Subjects, Authors, PressPackages, Profiles and Digests from raw JSON stored in database."

    def handle(self, *args, **options):
        try:
            ingest_logic.regenerate_all()

        except json.JSONDecodeError as err:
            LOG.error("failed to load your bad data: %s", err)
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
