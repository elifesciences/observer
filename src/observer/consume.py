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
    try:
        return requests_get(url, params).json()
    except requests.exceptions.RequestException as err:
        if not err.response.status_code == 404:
            # we expect 404s on unpublished content. everything else should be logged.
            context = {'url': url, 'params': params, 'user-params': user_params}
            LOG.error("failed to fetch %s: %s", endpoint, err, extra=context)
        raise err


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

# lsh@2022-02-01: this was such a bad idea. figure out how to get rid of it.
def content_type_from_endpoint(endpoint):
    """given an API endpoint like `press-packages/{id}` returns the singular value matching the constants in `models`.
    some endpoints are hardcoded to handle values that can't be derived."""
    return models.find_content_type(slugify(endpoint))

def single(endpoint, idfn=None, **kwargs):
    "consumes a single item from the API `endpoint` and creates/inserts it into the database."
    content_type = content_type_from_endpoint(endpoint)
    data = consume(endpoint.format_map(kwargs))
    idfn = idfn or default_idfn
    return upsert(idfn(data), content_type, data)

def all_items(endpoint, idfn=None, some_fn=None):
    """consumes all items from the given `endpoint` and then creates/inserts them into the database.
    items are inserted into the database in groups of 100.
    `idfn` is used to derive the value for `models.RawJSON.json_id`.

    if `some_fn` then per-page consumption is broken as soon as some_fn(item) returns False.
    whole page of results is upserted even if `some_fn` breaks part-way through results page.
    a list of `idfn(item)` is returned when `some_fn` is supplied."""
    initial = consume(endpoint, {'per-page': 1})
    per_page = 100
    num_pages = math.ceil(initial["total"] / float(per_page))
    idfn = idfn or default_idfn
    LOG.info("%s pages to fetch" % num_pages)

    try:
        do_upsert = True
        content_type = content_type_from_endpoint(endpoint)
    except KeyError:
        do_upsert = False

    accumulator = []
    accumulate = 100 # accumulate n pages before inserting
    id_accumulator = [] if some_fn else None
    break_iteration = False
    for page in range(1, num_pages + 1):
        try:
            resp = consume(endpoint, {'page': page, 'per-page': per_page})
        except requests.exceptions.RequestException:
            continue

        if some_fn:
            for item in resp['items']:
                if some_fn(item):
                    id_accumulator.append(idfn(item))
                else:
                    break_iteration = True

        accumulator.extend(resp['items'])

        if do_upsert and len(accumulator) >= accumulate:
            upsert_all(content_type, accumulator, idfn)
            accumulator = []

        if break_iteration:
            break

        # pause between requests to prevent flooding
        time.sleep(settings.SECONDS_BETWEEN_REQUESTS)

    # handle any leftovers
    if do_upsert and accumulator:
        upsert_all(content_type, accumulator, idfn)

    return id_accumulator
