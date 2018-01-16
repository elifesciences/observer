import sys
from os.path import join
from django.conf import settings
from django.core.management.base import BaseCommand
import logging
from observer import views

LOG = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'regenerates README.md in root of project'

    def handle(self, *args, **options):
        try:
            with open(join(settings.PROJECT_DIR, 'README.md'), 'w') as readme:
                readme.write(views.readme_markdown())
            LOG.info("wrote README.md")

        except:
            LOG.exception("unhandled exception attempting to write README.md file")
            raise

        sys.exit(0)
