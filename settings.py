"""
Django settings for commons project.
"""

from mayan.settings.base import *

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

ROOT_URLCONF = 'commons.urls'

WSGI_APPLICATION = 'commons.wsgi.application'

_file_path = os.path.abspath(os.path.dirname(__file__)).split('/')
BASE_DIR = '/'.join(_file_path[0:-1])
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "commons", "static"),
)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, "commons", "templates"),
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'commons',
        'USER': 'admin',
        'PASSWORD': 'giotto',
        'HOST': 'localhost',
        'PORT': '',
    }
}

ADMINS = (
    ('Giovanni Toffoli', 'toffoli@linkroma.it'),
)

# CONVERTER_GRAPHICS_BACKEND = 'converter.backends.graphicsmagick.GraphicsMagick'
