"""
Django settings for commons project.
"""

from mayan.settings.base import *

WSGI_APPLICATION = 'commons.wsgi.application'
ROOT_URLCONF = 'commons.urls'

# _file_path = os.path.abspath(os.path.dirname(__file__)).split('/')
# BASE_DIR = '/'.join(_file_path[0:-1])
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "commons", "static"),
)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, "commons", "templates"),
)

from private import *
