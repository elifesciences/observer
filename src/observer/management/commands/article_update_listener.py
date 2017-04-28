import sys, json
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
import logging
from observer import inc, ingest_logic
from observer.utils import lmap

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'open a connection to AWS SQS and listen for article update notifications'

    def handle(self, *args, **options):
        try:
            if not settings.ARTICLE_EVENT_QUEUE:
                raise ValueError("no queue name found. a queue name can be set in your 'app.cfg'. see example file 'elife.cfg'")

            def action(event):
                try:
                    LOG.debug("handling event %s" % event)
                    msid = json.loads(event)['id']
                    ingest_logic.download_article_versions(msid)
                    ingest_logic.regenerate(msid)

                except requests.exceptions.RequestException as err:
                    LOG.error("failed to fetch article %s: %s", msid, err)

                except BaseException as err:
                    LOG.exception("unhandled exception attempting to download and regenerate article %s", msid)

            LOG.info("attempting connection %s ...", settings.ARTICLE_EVENT_QUEUE)
            lmap(action, inc.poll(inc.queue(settings.ARTICLE_EVENT_QUEUE)))

        except ValueError as err:
            LOG.error(err)
            sys.exit(1)

        except:
            LOG.exception("unhandled exception attempting to ingest article")
            raise

        sys.exit(0)
