import sys, json
from django.conf import settings
from django.core.management.base import BaseCommand
import logging
from observer import inc
from observer.ingest_logic import download_regenerate_article, download_regenerate_presspackage

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'open a connection to AWS SQS and listen for update notifications'

    def handle(self, *args, **options):
        if not settings.EVENT_QUEUE:
            LOG.error("no queue name found. a queue name can be set in your 'app.cfg'. see example file 'elife.cfg'")
            sys.exit(1)

        LOG.info("attempting connection %s ...", settings.EVENT_QUEUE)

        def action(event):
            try:
                LOG.debug("handling event %s" % event)
                event = json.loads(event)
                objid = event['id']
                handlers = {
                    'article': download_regenerate_article,
                    'presspackage': download_regenerate_presspackage,
                }
                handlers[event['type']](objid)

            except BaseException as err:
                LOG.exception("unhandled exception attempting to handle event %s", event)

            return None # important, ensures results don't accumulate

        try:
            import newrelic.agent
            action = newrelic.agent.background_task()(action)
        except ImportError:
            pass

        # `any` doesn't accumulate a list of results in memory so long as
        # `action` returns false-y values.
        any(action(event) for event in inc.poll(inc.queue(settings.EVENT_QUEUE)))

        sys.exit(0)
