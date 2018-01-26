from collections import OrderedDict
import sys
from django.core.management.base import BaseCommand
from observer.ingest_logic import (
    download_all_article_versions, download_article_versions,
    download_all_article_metrics, download_article_metrics,
    regenerate_all, regenerate
)
from observer.utils import lmap, subdict
from functools import partial

LAX, METRICS = TARGETS = ['lax', 'elife-metrics']

class Command(BaseCommand):
    help = "a terrifically sequential and SLOW way to load ALL elife articles and versions"

    def add_arguments(self, parser):
        parser.add_argument('--msid', nargs='+', type=int, required=False)
        parser.add_argument('--target', nargs='+', required=False, choices=TARGETS)

    def handle(self, *args, **options):
        try:
            dl_ajson = download_all_article_versions
            dl_metrics = download_all_article_metrics
            regen = regenerate_all

            msidlist = options['msid']
            if msidlist:
                dl_ajson = partial(lmap, download_article_versions, msidlist)
                dl_metrics = partial(lmap, download_article_metrics, msidlist)
                regen = partial(lmap, regenerate, msidlist)

            targets = OrderedDict([
                (LAX, dl_ajson),
                (METRICS, dl_metrics),
            ])

            fnlist = (subdict(targets, options['target']) or targets).values()
            [fn() for fn in fnlist]

            regen()

        except KeyboardInterrupt:
            print("\nctrl-c caught, quitting.\ndownload progress has been saved")
            sys.exit(1)

        sys.exit(0)
