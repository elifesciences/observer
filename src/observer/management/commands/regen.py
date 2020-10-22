import sys, json
from django.core.management.base import BaseCommand
import logging
from observer import ingest_logic

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "regenerates all content from the raw JSON stored in the database."

    def handle(self, *args, **options):
        try:
            ingest_logic.regenerate_all()

        except json.JSONDecodeError as err:
            LOG.error("failed to load bad content: %s", err)
            sys.exit(1)

        except ingest_logic.StateError as err:
            LOG.error("failed to regenerate content: %s", err)
            sys.exit(1)

        except ValueError as err:
            LOG.error("failed to regenerate content, bad data: %s", err)
            sys.exit(1)

        except BaseException:
            LOG.exception("unhandled exception attempting to regenerate content")
            raise

        sys.exit(0)
