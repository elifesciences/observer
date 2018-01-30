from django.conf import settings
from django.views.decorators.cache import patch_cache_control
from django.utils.cache import patch_vary_headers

class DownstreamCaching(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        public_headers = {
            'public': True,

            # could probably bump these values to 10minutes.
            
            'max-age': 60 * 5, # 5 minutes, 300 seconds
            'stale-while-revalidate': 60 * 5, # 5 minutes, 300 seconds
            'stale-if-error': (60 * 60) * 24, # 1 day, 86400 seconds
        }
        private_headers = {
            'private': True,
            'max-age': 0, # seconds
            'must-revalidate': True,
        }

        # nothing currently sets the authenticated header or not
        authenticated = request.META.get(settings.KONG_AUTH_HEADER) 
        headers = public_headers if not authenticated else private_headers

        response = self.get_response(request)

        if not response.get('Cache-Control'):
            patch_cache_control(response, **headers)
        patch_vary_headers(response, ['Accept'])

        return response
