from datetime import datetime, timedelta
from collections import OrderedDict
import sys
from django.core.management.base import BaseCommand
from observer import ingest_logic, models, utils
from observer.utils import lmap, subdict
from functools import partial

LAX, METRICS, PRESSPACKAGES, PROFILES, DIGESTS, LABS_POSTS, COMMUNITY, PODCASTS, REVIEWED_PREPRINTS = \
    TARGETS = \
    ['lax', 'elife-metrics', 'press-packages', 'profiles', 'digests', 'labs-posts', 'community', 'podcasts', 'reviewed-preprints']

class Command(BaseCommand):
    help = "loads ALL elife articles and versions and metrics summary"

    def add_arguments(self, parser):
        parser.add_argument('--msid', nargs='+', required=False)
        parser.add_argument('--target', nargs='+', required=False, choices=TARGETS)
        parser.add_argument('--days', type=int, required=False)

    def handle(self, *args, **options):
        try:
            targetlist = options['target'] or TARGETS
            msidlist = options['msid']
            days = options['days']

            dl_ajson = ingest_logic.download_all_article_versions
            dl_metrics = ingest_logic.download_all_article_metrics
            dl_presspackages = partial(ingest_logic.download_all, models.PRESSPACKAGE)
            dl_profiles = partial(ingest_logic.download_all, models.PROFILE)
            dl_digests = partial(ingest_logic.download_all, models.DIGEST)
            dl_labs = partial(ingest_logic.download_all, models.LABS_POST)
            dl_community = partial(ingest_logic.download_all, models.COMMUNITY)
            dl_podcasts = partial(ingest_logic.download_all, models.PODCAST)
            dl_reviewed_preprints = partial(ingest_logic.download_all, models.REVIEWED_PREPRINT)

            if msidlist:
                dl_ajson = partial(lmap, ingest_logic.download_article_versions, msidlist)
                dl_metrics = partial(lmap, ingest_logic.download_article_metrics, msidlist)
                if LAX not in targetlist or METRICS not in targetlist:
                    # except articles and article-metrics, all other content is just a few pages to download,
                    # the extra complexity isn't worth it (yet).
                    # community is ~3 pages, digests is ~10
                    print("ignoring ID list, given content type doesn't support it.")

            if days:
                if targetlist != [LAX]:
                    print("the '--days' parameter is only compatible with '--target=lax' right now")
                    exit(1)

                cutoff = utils.todt(datetime.now()) - timedelta(days=days)
                print("cutoff date is: %s" % (utils.ymdhms(cutoff)))

                def some_fn(result):
                    "returns `True` when the versionDate for the given `result` falls within (now() - N days ago)."
                    pubdate = utils.todt(result['versionDate'])
                    res = pubdate >= cutoff
                    if res:
                        print("%s: %s" % (result['id'], result['versionDate']))
                    return res
                ingest_logic.download_regenerate_article_list(some_fn)
                exit(0)

            dl_targets = OrderedDict([
                (LAX, dl_ajson),
                (METRICS, dl_metrics),
                (PRESSPACKAGES, dl_presspackages),
                (PROFILES, dl_profiles),
                (DIGESTS, dl_digests),
                (LABS_POSTS, dl_labs),
                (COMMUNITY, dl_community),
                (PODCASTS, dl_podcasts),
                (REVIEWED_PREPRINTS, dl_reviewed_preprints),
            ])

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
            regen_podcasts = partial(ingest_logic.regenerate, models.PODCAST)
            regen_reviewed_preprints = partial(ingest_logic.regenerate, models.REVIEWED_PREPRINT)

            if msidlist:
                regen_articles = partial(lmap, ingest_logic.regenerate_article, msidlist)
                if LAX not in targetlist:
                    print("ignoring ID list, given content type doesn't support it or isn't implemented.")

            regen_targets = OrderedDict([
                (LAX, regen_articles),
                (PRESSPACKAGES, regen_presspackages),
                (PROFILES, regen_profiles),
                (DIGESTS, regen_digests),
                (LABS_POSTS, regen_labs_posts),
                (COMMUNITY, regen_community),
                (PODCASTS, regen_podcasts),
                (REVIEWED_PREPRINTS, regen_reviewed_preprints),
            ])

            for content_type, fn in subdict(regen_targets, targetlist).items():
                print('regenerate %r' % content_type)
                fn()

        except KeyboardInterrupt:
            print("\nctrl-c caught, quitting.\ndownload progress has been saved")
            sys.exit(1)

        sys.exit(0)
