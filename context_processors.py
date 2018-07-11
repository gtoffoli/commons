from datetime import datetime
from django.conf import settings
from django.contrib.sessions.models import Session

def online_users_count():
    try:
        return Session.objects.filter(expire_date__gte = datetime.now()).count()
        #return Session.objects.filter(expire_date__gte = timezone.now()).count()
    except:
        return 0

# def sitename(request):
def processor(request):
    path = request.path
    protocol = request.is_secure() and 'https' or 'http'
    for language in settings.LANGUAGES:
        # path = path.replace('/%s' % language[0], '')
        path = path.replace('/%s/' % language[0], '/')
    return {
        'site_name': settings.SITE_NAME,
        'users_count': online_users_count(),
        'path_no_language': path,
        'PRODUCTION': settings.PRODUCTION,
        'PROTOCOL': protocol,
        'HAS_SAML2': settings.HAS_SAML2,
        'HAS_XMPP': settings.HAS_XMPP,
        'HAS_DMUC': settings.HAS_DMUC,
        'HAS_ZINNIA': settings.HAS_ZINNIA,
        'DJANGO_VERSION': settings.DJANGO_VERSION,
    }
