import sys
from django.core.management.base import BaseCommand
import logging
from observer import views

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'regenerates README.md in root of project'

    def handle(self, *args, **options):
        try:
            self.stdout.write(views.readme_markdown())
        except BaseException:
            LOG.exception("unhandled exception attempting to write README.md file")
            raise

        sys.exit(0)
