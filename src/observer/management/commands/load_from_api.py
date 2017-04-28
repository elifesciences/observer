import sys
from django.core.management.base import BaseCommand
import math
import requests
from collections import OrderedDict
from observer.ingest_logic import upsert_ajson, regenerate_all
from observer.utils import lmap
from django.conf import settings
import requests_cache
from datetime import timedelta
import logging

LOG = logging.getLogger(__name__)

requests_cache.install_cache(**{
    'cache_name': '/tmp/api-cache',
    'backend': 'sqlite',
    'fast_save': True,
    'extension': '.sqlite3',
    # https://requests-cache.readthedocs.io/en/latest/user_guide.html#expiration
    'expire_after': timedelta(hours=24)
})

def consume(endpoint, usrparams={}):
    params = {'per-page': 100, 'page': 1}
    params.update(usrparams)
    url = settings.API_URL + "/" + endpoint.strip('/')
    LOG.info('fetching %s params %s' % (url, params))
    resp = requests.get(url, params)
    resp.raise_for_status()
    return resp.json()

def fname(ajson):
    return "elife-%s-v%s.json" % (ajson["id"], ajson["version"])

def download_snippets():
    ini = consume("articles", {'per-page': 1})
    per_page = 100.0
    num_pages = math.ceil(ini["total"] / per_page)
    msid_ver_idx = OrderedDict() # ll: {09560: 1, ...}
    LOG.info("%s pages to fetch" % num_pages)
    for page in range(1, num_pages):
        resp = consume("articles", {'page': page})
        for snippet in resp["items"]:
            msid_ver_idx[snippet["id"]] = snippet["version"]
    return msid_ver_idx

def download_all_article_versions():
    try:
        msid_ver_idx = download_snippets()

        LOG.info("%s articles to fetch" % len(msid_ver_idx))
        idx = sorted(msid_ver_idx.items(), key=lambda x: x[0], reverse=True)
        for msid, latest_version in idx:
            LOG.info(' %s versions to fetch' % latest_version)

            # download each version and stick into observer
            version_range = range(1, latest_version + 1)
            lmap(lambda version: upsert_ajson(consume("articles/%s/versions/%s" % (msid, version))), version_range)

    except KeyboardInterrupt:
        print("\nctrl-c caught, quitting.\ndownload progress has been saved")
        sys.exit(1)


class Command(BaseCommand):
    help = "a terrifically sequential and SLOW way to load ALL elife articles and versions"

    def handle(self, *args, **options):
        download_all_article_versions()
        regenerate_all()
        sys.exit(0)
