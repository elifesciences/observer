import sys
from django.conf import settings
from django.core.management.base import BaseCommand
import logging
from observer import inc

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'open a connection to AWS SQS and listen for update notifications'

    def handle(self, *args, **options):
        if not settings.EVENT_QUEUE:
            LOG.error("no queue name found. a queue name can be set in your 'app.cfg'. see example file 'elife.cfg'")
            sys.exit(1)

        LOG.info("attempting connection %s ...", settings.EVENT_QUEUE)

        # `any` doesn't accumulate a list of results in memory so long as
        # `action` returns false-y values.
        any(inc.handler(event) for event in inc.poll(inc.queue(settings.EVENT_QUEUE)))

        sys.exit(0)
