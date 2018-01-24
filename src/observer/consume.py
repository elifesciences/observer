import backoff, requests, requests_cache
from datetime import timedelta
from django.conf import settings
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
