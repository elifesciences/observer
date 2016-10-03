import sys, json, argparse
from django.core.management.base import BaseCommand
import logging
from observer import logic

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'ingest article-json from a file or stdin'

    def add_arguments(self, parser):
        parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)

    def handle(self, *args, **options):
        self.log_context = {}

        try:
            article_json = options['infile'].read()
            self.log_context['data'] = str(article_json[:25]) + "... (truncated)" if article_json else ''
            article_data = json.loads(article_json)
        except json.JSONDecodeError as err:
            LOG.error("could not decode the json you gave me: %r for data: %r", err, article_json)
            sys.exit(1)

        # REMOVE: this is a hack because the version isn't available in the article-json we're using yet
        if not article_data['article'].get('version'):
            _, ver = logic.pathdata(options['infile'].name)
            article_data['article']['version'] = ver
            
        try:
            artobj, created, updated = logic.upsert_article_json(article_data, {})
            LOG.info("art %s created=%s, updated=%s" % (artobj.msid, created, updated))

        except logic.StateError as err:
            LOG.error("failed to ingest article: %s", err)
            sys.exit(1)

        except:
            LOG.exception("unhandled exception attempting to ingest article", extra=self.log_context)
            raise

        sys.exit(0)
