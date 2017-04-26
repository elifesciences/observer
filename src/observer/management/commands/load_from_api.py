import sys
from django.core.management.base import BaseCommand
import math
import requests
from collections import OrderedDict
from observer.ingest_logic import upsert_ajson, regenerate_many

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
    url = "https://prod--gateway.elifesciences.org/" + endpoint.strip('/')
    LOG.info('fetching %s params %s' % (url, params))
    resp = requests.get(url, params)
    if resp.status_code == 200:
        return resp.json()
    return resp

def fname(ajson):
    return "elife-%s-v%s.json" % (ajson["id"], ajson["version"])

def download_all_article_versions():
    ini = consume("articles", {'per-page': 1})
    per_page = 100.0
    num_pages = math.ceil(ini["total"] / per_page)
    msid_ver_idx = OrderedDict() # ll: {09560: 1, ...}
    LOG.info("%s pages to fetch" % num_pages)
    try:
        for page in range(1, num_pages):
            resp = consume("articles", {'page': page})
            for snippet in resp["items"]:
                msid_ver_idx[snippet["id"]] = snippet["version"]

        LOG.info("%s articles to fetch" % len(msid_ver_idx))
        for msid, latest_version in msid_ver_idx.items():
            LOG.info(' %s versions to fetch' % latest_version)
            for version in range(1, latest_version + 1):
                # download and stick into observer
                upsert_ajson(consume("articles/%s/versions/%s" % (msid, version)))

    except KeyboardInterrupt:
        print("\nctrl-c caught, quitting.\ndownload progress has been saved")
        sys.exit(1)

    return msid_ver_idx.keys()


class Command(BaseCommand):
    help = "a terrifically sequential and SLOW way to load ALL elife articles and versions"

    def add_arguments(self, parser):
        #parser.add_argument('--target', required=True, action='store')
        pass

    def handle(self, *args, **options):
        msid_list = download_all_article_versions()
        regenerate_many(msid_list)
        sys.exit(0)
