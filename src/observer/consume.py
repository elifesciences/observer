import backoff, requests, requests_cache
from . import utils, models
from slugify import slugify
import math
from datetime import timedelta
from django.conf import settings
from django.db import transaction
import logging

LOG = logging.getLogger(__name__)

logging.getLogger('backoff').setLevel(logging.CRITICAL)

if settings.DEBUG:
    requests_cache.install_cache(**{
        'cache_name': '/tmp/api-cache',
        'backend': 'sqlite',
        'fast_save': True,
        'extension': '.sqlite3',
        # https://requests-cache.readthedocs.io/en/latest/user_guide.html#expiration
        'expire_after': timedelta(hours=24)
    })

def _giveup(err):
    "accepts the exception and returns a truthy value if the exception should not be retried"
    if err.response.status_code == 404:
        # too noisy
        #LOG.warn("object at %s not found, not re-attempting request", err)
        return True

def _giving_up(details):
    LOG.warn("request %s failed after %s attempts", details['args'][0], details['tries'])

def _retrying(details):
    LOG.warn("re-attempting request: %s", details['args'][0])

@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=5,
    giveup=_giveup,
    on_backoff=_retrying,
    on_giveup=_giving_up)
def requests_get(*args, **kwargs):
    "requests.get wrapper that handles attempts to re-try a request on error EXCEPT on 404 responses"
    resp = requests.get(*args, **kwargs)
    resp.raise_for_status()
    return resp

def consume(endpoint, usrparams={}):
    params = {'per-page': 100, 'page': 1}
    params.update(usrparams)
    url = settings.API_URL + "/" + endpoint.strip('/')
    LOG.info('fetching %s params %s' % (url, params))
    return requests_get(url, params).json()

#
#
#

def default_idfn(row):
    return row['id']

def upsert(iid, content_type, content):
    data = {
        'msid': iid,
        'version': None,
        'ajson': content,
        'ajson_type': content_type
    }
    return utils.create_or_update(models.ArticleJSON, data, ['msid'])

def upsert_all(content_type, rows, idfn):
    def do_safely(row):
        try:
            iid = idfn(row)
        except Exception:
            LOG.error("failed to extract item id from row: %s", row)
            return
        return upsert(iid, content_type, row)

    with transaction.atomic():
        utils.lmap(do_safely, rows)
    return None

#
# generic content consumption
#

def content_type_from_endpoint(endpoint):
    """given an API `endpoint` like `press-packages/{id}`, returns a slugified version like `press-packages-id`.
    if a given API `endpoint` doesn't exist, it's value is looked up in a map of aliases.
    for example, `digests` is aliased `digests-id`."""
    val = slugify(endpoint) # press-packages/{id} => press-packages-id
    aliases = {
        # summary endpoints
        'profiles': models.PROFILE,
        'press-packages': models.PRESSPACKAGE,
        'digests': models.DIGEST,

        # backwards support
        'articles-id-versions-version': models.LAX_AJSON,
        'metrics-article-summary': models.METRICS_SUMMARY
    }
    return aliases.get(val, val)

def single(endpoint, idfn=None, **kwargs):
    content_type = content_type_from_endpoint(endpoint)
    try:
        data = consume(endpoint.format_map(kwargs))
    except requests.exceptions.RequestException as err:
        LOG.error("failed to fetch %s: %s", endpoint, err)
        raise err

    idfn = idfn or default_idfn
    return upsert(idfn(data), content_type, data)

def all_items(endpoint, idfn=None, **kwargs):
    initial = consume(endpoint, {'per-page': 1})
    per_page = 100
    num_pages = math.ceil(initial["total"] / float(per_page))
    idfn = idfn or default_idfn
    LOG.info("%s pages to fetch" % num_pages)

    content_type = content_type_from_endpoint(endpoint)

    accumulator = []
    accumulate = 100 # accumulate 10 pages before inserting
    for page in range(1, num_pages + 1):
        try:
            resp = consume(endpoint, {'page': page, 'per-page': per_page})
        except requests.exceptions.RequestException as err:
            LOG.error("failed to fetch %s: %s", endpoint, err)
            continue

        accumulator.extend(resp['items'])

        if len(accumulator) >= accumulate:
            upsert_all(content_type, accumulator, idfn)
            accumulator = []

    # handle any leftovers
    if accumulator:
        upsert_all(content_type, accumulator, idfn)

    return None
