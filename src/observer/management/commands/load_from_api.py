import sys
from django.core.management.base import BaseCommand
from observer.ingest_logic import download_all_article_versions, regenerate_all

class Command(BaseCommand):
    help = "a terrifically sequential and SLOW way to load ALL elife articles and versions"

    def handle(self, *args, **options):
        try:
            download_all_article_versions()
            regenerate_all()
        except KeyboardInterrupt:
            print("\nctrl-c caught, quitting.\ndownload progress has been saved")
            sys.exit(1)

        sys.exit(0)
