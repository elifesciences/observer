from collections import OrderedDict
import sys
from django.core.management.base import BaseCommand
from observer import ingest_logic, models
from observer.utils import lmap, subdict
from functools import partial

LAX, METRICS, PRESSPACKAGES, PROFILES, DIGESTS, LABS_POST, COMMUNITY = \
    TARGETS = \
    ['lax', 'elife-metrics', 'press-packages', 'profiles', 'digests', 'labs-posts', 'community']

class Command(BaseCommand):
    help = "loads ALL elife articles and versions and metrics summary"

    def add_arguments(self, parser):
        parser.add_argument('--msid', nargs='+', required=False)
        parser.add_argument('--target', nargs='+', required=False, choices=TARGETS)

    def handle(self, *args, **options):
        try:
            targetlist = options['target'] or TARGETS
            msidlist = options['msid']

            if len(targetlist) > 1 and msidlist:
                print('cannot mix and match targets and lists of ids.')
                print('choose one target and many IDs or many targets and no IDs')
                exit(1)

            dl_ajson = ingest_logic.download_all_article_versions
            dl_metrics = ingest_logic.download_all_article_metrics
            dl_presspackages = partial(ingest_logic.download_all, models.PRESSPACKAGE)
            dl_profiles = partial(ingest_logic.download_all, models.PROFILE)
            dl_digests = partial(ingest_logic.download_all, models.DIGEST)
            dl_labs = partial(ingest_logic.download_all, models.LABS_POST)
            dl_community = partial(ingest_logic.download_all, models.COMMUNITY)

            dl_targets = OrderedDict([
                (LAX, dl_ajson),
                (METRICS, dl_metrics),
                (PRESSPACKAGES, dl_presspackages),
                (PROFILES, dl_profiles),
                (DIGESTS, dl_digests),
                (LABS_POST, dl_labs),
                (COMMUNITY, dl_community),
            ])

            if msidlist:
                dl_ajson = partial(lmap, ingest_logic.download_article_versions, msidlist)
                dl_metrics = partial(lmap, ingest_logic.download_article_metrics, msidlist)
                if LAX not in targetlist or METRICS not in targetlist:
                    # except articles and article-metrics, all other content is just a few pages to download,
                    # the extra complexity isn't worth it (yet).
                    # community is ~3 pages, digests is ~10
                    print("ignoring ID list, given content type doesn't support it.")

            for content_type, fn in subdict(dl_targets, targetlist).items():
                print('downloading %r' % content_type)
                fn()

            # regenerate

            regen_articles = ingest_logic.regenerate_all_articles
            # regen_metrics = ... # included in article metrics
            regen_presspackages = partial(ingest_logic.regenerate, models.PRESSPACKAGE)
            regen_profiles = partial(ingest_logic.regenerate, models.PROFILE)
            regen_digests = partial(ingest_logic.regenerate, models.DIGEST)
            regen_labs_posts = partial(ingest_logic.regenerate, models.LABS_POST)
            regen_community = partial(ingest_logic.regenerate, models.COMMUNITY) # includes features, blog posts, interviews, etc

            regen_targets = OrderedDict([
                (LAX, regen_articles),
                (PRESSPACKAGES, regen_presspackages),
                (PROFILES, regen_profiles),
                (DIGESTS, regen_digests),
                (LABS_POST, regen_labs_posts),
                (COMMUNITY, regen_community),
            ])

            if msidlist:
                regen_articles = partial(lmap, ingest_logic.regenerate_article, msidlist)
                if LAX not in targetlist:
                    # actually, I'm just too lazy right now
                    print("ignoring ID list, given content type doesn't support it.")

            for content_type, fn in subdict(regen_targets, targetlist).items():
                print('regenerate %r' % content_type)
                fn()

        except KeyboardInterrupt:
            print("\nctrl-c caught, quitting.\ndownload progress has been saved")
            sys.exit(1)

        sys.exit(0)
