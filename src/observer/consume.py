import time
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
        return True

def _giving_up(details):
    LOG.warn("request %s failed after %s attempts", details['args'][0], details['tries'])

def _retrying(details):
    LOG.warn("re-attempting request: %s", details['args'][0])

@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=10,
    giveup=_giveup,
    on_backoff=_retrying,
    on_giveup=_giving_up,
    max_time=300 # seconds, 5mins
)
def requests_get(*args, **kwargs):
    "requests.get wrapper that handles attempts to re-try a request on error EXCEPT on 404 responses"
    headers = kwargs.pop('headers', {})
    headers['user-agent'] = 'observer/unreleased (https://github.com/elifesciences/observer)'
    kwargs['headers'] = headers
    resp = requests.get(*args, **kwargs)
    resp.raise_for_status()
    return resp

def consume(endpoint, user_params={}):
    params = {'per-page': 100, 'page': 1}
    params.update(user_params)
    url = settings.API_URL + "/" + endpoint.strip('/')
    LOG.info('fetching %s params %s' % (url, params))
    return requests_get(url, params).json()

#
#
#

def default_idfn(row):
    return row['id']

def upsert(iid, json_type, content):
    data = {
        'msid': iid,
        'version': None,
        'json': content,
        'json_type': json_type
    }
    return utils.create_or_update(models.RawJSON, data, ['msid', 'json_type'])

def upsert_all(json_type, rows, idfn):
    def do_safely(row):
        try:
            item_id = idfn(row)
        except Exception:
            LOG.error("failed to extract item id from row: %s", row)
            return
        return upsert(item_id, json_type, row)

    with transaction.atomic():
        utils.lmap(do_safely, rows)
    return None

#
# generic content consumption
#

# todo: this was such a bad idea. figure out how to get rid of it.
def content_type_from_endpoint(endpoint):
    """given an API `endpoint` like `press-packages/{id}`, returns a slugified version like `press-packages-id`.
    if the given API `endpoint` doesn't exist in the alias map, it's value is returned as-is."""

    # "press-packages/{id}" => "press-packages-id", "interviews" => "interviews"
    val = slugify(endpoint)
    aliases = {
        # models.PODCAST == 'podcast' and not 'podcast-episode' :(
        'podcast-episodes': models.PODCAST,
        'podcast-episodes/{id}': models.PODCAST,

        # models.PRESSPACKAGE == 'press-packages-id' :(
        'press-packages-id': models.PRESSPACKAGE,
        'press-packages': models.PRESSPACKAGE,

        # models.PROFILE == 'profiles-id' :(
        # as of 2022-01-31 we have 47k 'profiles-id' in RawJSON
        'profiles': models.PROFILE,
        'profiles-id': models.PROFILE,

        # "/articles/{id}/versions/{version}"
        'articles-id-versions-version': models.LAX_AJSON, # 'lax-ajson'

        # "/metrics/article-summary" (non-api)
        'metrics-article-summary': models.METRICS_SUMMARY, # 'elife-metrics-summary'
    }
    alias = aliases.get(slugify(endpoint))
    if alias:
        return alias

    # at this point val will either be an alias as above, or something like "/profiles/{id}"
    # we don't want "foo-id" with the "-id" suffix *at all*

    val = val.strip("/") # just in case. "/digests/{id}" => "digests/{id}"

    # at this point val will either be "digests" (api summary) or "digests/{id}" (api detail)
    if "/" in val:
        val = val[:val.index("/")] # "digests/{id}" => "digests"

    # now, we don't want the plural version stored in the database, we use the singular internally
    # i.e. models.DIGEST is 'digest' not 'digests'

    val = val.rstrip('s')

    return val

def single(endpoint, idfn=None, **kwargs):
    "consumes a single item from the API `endpoint` and creates/inserts it into the database."
    content_type = content_type_from_endpoint(endpoint)
    try:
        data = consume(endpoint.format_map(kwargs))
    except requests.exceptions.RequestException as err:
        LOG.error("failed to fetch %s: %s", endpoint, err)
        raise err

    idfn = idfn or default_idfn
    return upsert(idfn(data), content_type, data)

def all_items(endpoint, idfn=None, **kwargs):
    """consumes all items from the given `endpoint` and then creates/inserts them into the database.
    items are inserted into the database in groups of 100.
    `idfn` is used to derive the value for `models.RawJSON.json_id`."""
    initial = consume(endpoint, {'per-page': 1})
    per_page = 100
    num_pages = math.ceil(initial["total"] / float(per_page))
    idfn = idfn or default_idfn
    LOG.info("%s pages to fetch" % num_pages)

    content_type = content_type_from_endpoint(endpoint)

    accumulator = []
    accumulate = 100 # accumulate n pages before inserting
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

        # pause between requests to prevent flooding
        time.sleep(settings.SECONDS_BETWEEN_REQUESTS)

    # handle any leftovers
    if accumulator:
        upsert_all(content_type, accumulator, idfn)

    return None
