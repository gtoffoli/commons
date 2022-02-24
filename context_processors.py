from datetime import datetime
from django.conf import settings
from django.contrib.sessions.models import Session

def online_users_count():
    try:
        return Session.objects.filter(expire_date__gte = datetime.now()).count()
    except:
        return 0

def processor(request):
    path = request.path
    protocol = request.is_secure() and 'https' or 'http'
    host = request.META.get('HTTP_HOST', '')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    browser = user_agent.count('Firefox') and 'Firefox' or user_agent
    is_primary_domain = False
    is_secondary_domain = False
    is_test_domain = False
    # if host == settings.PRIMARY_DOMAIN:
    if host == settings.PRIMARY_DOMAIN or host.count('localhost'):
        is_primary_domain = True
    elif host == settings.SECONDARY_DOMAIN:
        is_secondary_domain = True
    elif host == settings.TEST_DOMAIN:
        is_test_domain = True
    for code, name in settings.LANGUAGES:
        if path.startswith('/' + code + '/'):
            path = path[len(code)+1:]
            break
    canonical = '%s://%s%s' % (protocol, settings.PRIMARY_DOMAIN, path)
    user = request.user
    inbox_count = 0
    if user.is_authenticated:
        from django_messages.models import inbox_count_for
        inbox_count = inbox_count_for(user)
    return {
        'site_name': settings.SITE_NAME,
        'users_count': online_users_count(),
        'path_no_language': path,
        'PRODUCTION': settings.PRODUCTION,
        'PROTOCOL': protocol,
        'HOST': host,
        'is_primary_domain': is_primary_domain,
        'is_secondary_domain': is_secondary_domain,
        'is_test_domain': is_test_domain,
        'DOMAIN': host,
        'CANONICAL': canonical,
        'HAS_LINKEDIN_AUTHENTICATION': settings.HAS_LINKEDIN_AUTHENTICATION,
        'HAS_FACEBOOK_AUTHENTICATION': settings.HAS_FACEBOOK_AUTHENTICATION,
        'HAS_SOCIAL_AUTHENTICATION': settings.HAS_LINKEDIN_AUTHENTICATION or settings.HAS_FACEBOOK_AUTHENTICATION,
        'HAS_SAML2': settings.HAS_SAML2,
        'HAS_LRS': settings.HAS_LRS,
        'HAS_MEETING': settings.HAS_MEETING,
        'HAS_ZINNIA': settings.HAS_ZINNIA,
        'INBOX_COUNT': inbox_count,
        'BROWSER': browser,
        'SITE_ID': settings.SITE_ID,
        'HAS_CALENDAR': settings.HAS_CALENDAR,
    }
