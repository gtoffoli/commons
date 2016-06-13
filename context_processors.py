from datetime import datetime
from django.conf import settings
from django.contrib.sessions.models import Session

def online_users_count():
    return Session.objects.filter(expire_date__gte = datetime.now()).count()
    #return Session.objects.filter(expire_date__gte = timezone.now()).count()

# def sitename(request):
def processor(request):
    return {
        'site_name': settings.SITE_NAME,
        'users_count': online_users_count(),
    }
