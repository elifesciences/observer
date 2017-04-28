import sys
from django.conf import settings
from django.core.management.base import BaseCommand
import logging
from observer import inc

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'open a connection to AWS SQS and listen for article update notifications'

    def handle(self, *args, **options):
        try:
            if not settings.ARTICLE_EVENT_QUEUE:
                raise ValueError("no queue name found. a queue name can be set in your 'app.cfg'. see example file 'elife.cfg'")
            inc.poll(inc.queue(settings.ARTICLE_EVENT_QUEUE))

        except ValueError as err:
            LOG.error(err)
            sys.exit(1)

        except:
            LOG.exception("unhandled exception attempting to ingest article", extra=self.log_context)
            raise

        sys.exit(0)
