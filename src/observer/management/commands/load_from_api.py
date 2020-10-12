from collections import OrderedDict
import sys
from django.core.management.base import BaseCommand
from observer import ingest_logic
from observer.utils import lmap, subdict
from functools import partial

LAX, METRICS, PRESSPACKAGES, PROFILES, DIGESTS = TARGETS = ['lax', 'elife-metrics', 'press-packages', 'profiles', 'digests']

class Command(BaseCommand):
    help = "loads ALL elife articles and versions and metrics summary"

    def add_arguments(self, parser):
        parser.add_argument('--msid', nargs='+', type=int, required=False)
        parser.add_argument('--target', nargs='+', required=False, choices=TARGETS)

    def handle(self, *args, **options):
        try:
            dl_ajson = ingest_logic.download_all_article_versions
            dl_metrics = ingest_logic.download_all_article_metrics
            dl_presspackages = ingest_logic.download_all_presspackages
            dl_profiles = ingest_logic.download_all_profiles
            dl_digests = ingest_logic.download_all_digests
            regen = ingest_logic.regenerate_all

            # TODO: observer isn't as article-centric any more
            # this section might need altering
            msidlist = options['msid']
            if msidlist:
                dl_ajson = partial(lmap, ingest_logic.download_article_versions, msidlist)
                dl_metrics = partial(lmap, ingest_logic.download_article_metrics, msidlist)
                # dl_presspackages = ...
                # dl_profiles = ...
                regen = partial(lmap, ingest_logic.regenerate_article, msidlist)

            targets = OrderedDict([
                (LAX, dl_ajson),
                (METRICS, dl_metrics),
                (PRESSPACKAGES, dl_presspackages),
                (PROFILES, dl_profiles),
                (DIGESTS, dl_digests),
            ])

            targetlist = options['target'] or []
            fnlist = (subdict(targets, targetlist) or targets).values()
            [fn() for fn in fnlist]

            regen()

        except KeyboardInterrupt:
            print("\nctrl-c caught, quitting.\ndownload progress has been saved")
            sys.exit(1)

        sys.exit(0)
