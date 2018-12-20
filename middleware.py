from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

if settings.DJANGO_VERSION > 1:
    from  django.utils.deprecation import MiddlewareMixin
    class ActiveUserMiddleware(MiddlewareMixin):
        pass
else:
    class ActiveUserMiddleware:
        pass

def process_request(self, request):
    user = request.user
    print (user.is_authenticated, user.username)
    if user.is_authenticated:
        now = timezone.now()
        cache.set('seen_%s' % (user.username), now, 
                       settings.USER_LASTSEEN_TIMEOUT)

ActiveUserMiddleware.process_request = process_request