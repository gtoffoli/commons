from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

class ActiveUserMiddleware:

    def process_request(self, request):
        user = request.user
        if user.is_authenticated():
            now = timezone.now()
            cache.set('seen_%s' % (user.username), now, 
                           settings.USER_LASTSEEN_TIMEOUT)
