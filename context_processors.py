from django.conf import settings

def sitename(request):
    return {
        'site_name': settings.SITE_NAME
    }
