from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from  django.utils.deprecation import MiddlewareMixin
class ActiveUserMiddleware(MiddlewareMixin):
    pass

def process_request(self, request):
    user = request.user
    if user.is_authenticated:
        now = timezone.now()
        cache.set('seen_%s' % (user.username), now, 
                       settings.USER_LASTSEEN_TIMEOUT)

ActiveUserMiddleware.process_request = process_request

# see https://docs.djangoproject.com/en/2.2/topics/http/middleware/ and https://www.techiediaries.com/django-cors/
class CorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before the view (and later middleware) are called.
        response = self.get_response(request)
        # Code to be executed for each request/response after the view is called.
        response["Access-Control-Allow-Origin"] = "*"
        return response

class EmbeddedMiddleware(MiddlewareMixin):
    pass

    def process_response(self, request, response):
        embedded_cookie_changed = getattr(request, 'embedded_cookie_changed', '')
        if embedded_cookie_changed:
            EMBEDDED = getattr(request, 'EMBEDDED')
            response["Access-Control-Allow-Headers"] = "true"
            response.set_cookie('EMBEDDED', EMBEDDED, max_age=3600)
        return response
