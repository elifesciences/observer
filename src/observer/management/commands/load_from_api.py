from collections import OrderedDict
import sys
from django.core.management.base import BaseCommand
from observer import ingest_logic, models
from observer.utils import lmap, subdict
from functools import partial

LAX, METRICS, PRESSPACKAGES, PROFILES, DIGESTS, LABS_POST = TARGETS = ['lax', 'elife-metrics', 'press-packages', 'profiles', 'digests', 'labs-posts']

class Command(BaseCommand):
    help = "loads ALL elife articles and versions and metrics summary"

    def add_arguments(self, parser):
        parser.add_argument('--msid', nargs='+', type=int, required=False)
        parser.add_argument('--target', nargs='+', required=False, choices=TARGETS)

    def handle(self, *args, **options):
        try:
            targetlist = options['target'] or []
            msidlist = options['msid']

            if len(targetlist) > 1 and msidlist:
                print('cannot mix and match targets and lists of ids.')
                print('choose one target and many IDs or many targets and no IDs')
                exit(1)

            dl_ajson = ingest_logic.download_all_article_versions
            dl_metrics = ingest_logic.download_all_article_metrics
            dl_presspackages = partial(ingest_logic.download_all, models.PRESSPACKAGE)
            dl_profiles = ingest_logic.download_all_profiles
            dl_digests = ingest_logic.download_all_digests
            dl_labs = partial(ingest_logic.download_all, models.LABS_POST)

            regen = ingest_logic.regenerate_all

            # TODO: observer isn't as article-centric any more
            # this section might need altering
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
                (LABS_POST, dl_labs),
            ])

            fnlist = (subdict(targets, targetlist) or targets).values()
            [fn() for fn in fnlist]

            regen()

        except KeyboardInterrupt:
            print("\nctrl-c caught, quitting.\ndownload progress has been saved")
            sys.exit(1)

        sys.exit(0)
