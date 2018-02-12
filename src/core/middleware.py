from django.views.decorators.cache import patch_cache_control
from django.utils.cache import patch_vary_headers

MAX_AGE = 60 * 5
MAX_STALE = (60 * 60) * 24

class DownstreamCaching(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        headers = {
            'public': True,

            # could probably bump these values to 10minutes.

            'max-age': MAX_AGE, # 5 minutes, 300 seconds
            'stale-while-revalidate': MAX_AGE, # 5 minutes, 300 seconds
            'stale-if-error': MAX_STALE, # 1 day, 86400 seconds
        }
        response = self.get_response(request)

        if not response.get('Cache-Control'):
            patch_cache_control(response, **headers)
        patch_vary_headers(response, ['Accept'])

        return response
