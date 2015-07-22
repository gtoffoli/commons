# -*- coding: utf-8 -*-"""
"""
Django settings for commons project.
"""

from django.utils.translation import ugettext_lazy as _

PRODUCTION = False
DEBUG_TOOLBAR= False
# from mayan.settings.base import *
# from base import *

import os
import sys

from private import *

if PRODUCTION:
    DEBUG = False
    ALLOWED_HOSTS = ['*']
else:
    DEBUG = True
    # TEMPLATE_STRING_IF_INVALID = '%s'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'om^a(i8^6&h+umbd2%pt91cj!qu_@oztw117rgxmn(n2lp^*c!'

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
)
if DEBUG and DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE_CLASSES

INSTALLED_APPS = (
    # Django
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.comments',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    # 3rd party
    # 'compressor',
    'corsheaders',
    'djcelery',
    'filetransfers',
    'mptt',
    'rest_framework',
    'rest_framework.authtoken',
    'solo',
    # 'south',
    # Base generic
    'acls',
    'permissions',
    'user_management',
    # Mayan EDMS
    'checkouts',
    'document_acls',
    'documents',
    'metadata',
    'events',
    # extend auth model
    "hierarchical_auth",
    "django_extensions",
    "datetimewidget",
    # django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # ... include the providers you want to enable:
    'allauth.socialaccount.providers.facebook',
    'tinymce',
    # theme (from pinax project)
    "pinax_theme_bootstrap",
    "bootstrapform",
    # pinax starter project ?
    "pinax",
    # menus and ...
    'menu',
    'taggit',
    'taggit_live',
    'datatrans',
    # commons project
    'django_messages',
    'roles',
    'django_dag',
    'commons',
    # Placed after rest_api to allow template overriding
    # Must be last on Django < 1.7 as per documentation
    # https://django-activity-stream.readthedocs.org/en/latest/installation.html
    'actstream',
)
if DEBUG and DEBUG_TOOLBAR:
    INSTALLED_APPS = list(INSTALLED_APPS) + ['debug_toolbar']

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    # theme (from pinax project)
    "pinax_theme_bootstrap.context_processors.theme",
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

# in development, disable template caching
# if os.name == 'nt':
if not PRODUCTION:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )

# ========= FROM MAYAN

# --------- Pagination ----------------
PAGINATION_INVALID_PAGE_RAISES_404 = True
# ---------- Search ------------------
SEARCH_SHOW_OBJECT_TYPE = False
# ---------- Django REST framework -----------
REST_FRAMEWORK = {
    'PAGINATE_BY': 10,
    'PAGINATE_BY_PARAM': 'page_size',
    'MAX_PAGINATE_BY': 100,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    )
}
# ----------- Celery ----------
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'
# ------------ CORS ------------
CORS_ORIGIN_ALLOW_ALL = True
# ------ Django REST Swagger -----
SWAGGER_SETTINGS = {
    'api_version': '0',  # Specify your API's version
}

# ========= MAYAN'S IMPROVEMENTS

# --------- CONVERTERS ----------------
if os.name == 'nt':
    CONVERTER_IM_CONVERT_PATH = '\\Program Files\\ImageMagick-6.9.0-Q8\\convert.exe'
    CONVERTER_IM_IDENTIFY_PATH = '\\Program Files\\ImageMagick-6.9.0-Q8\\identify.exe'
    CONVERTER_GM_PATH = '\\Program Files\\GraphicsMagick-1.3.21-Q8\\gm.exe'
    CONVERTER_LIBREOFFICE_PATH = '/usr/bin/libreoffice'
    CONVERTER_PDFTOPPM_PATH = '\\Program Files\\xpdf\\pdftopng.exe'
else:
    CONVERTER_IM_CONVERT_PATH = '/usr/bin/convert'
    CONVERTER_IM_IDENTIFY_PATH = '/usr/bin/identify'
    CONVERTER_GM_PATH = '/usr/bin/gm'
    CONVERTER_LIBREOFFICE_PATH = '/usr/bin/libreoffice'
    CONVERTER_PDFTOPPM_PATH = '/usr/bin/pdftoppm'

# ========= DON'T KNOW WHY THIS NEEDED

import mayan.apps
sys.path.append(os.path.dirname(os.path.abspath(mayan.apps.__file__)))

# ========= COMMONS' CUSTOMIZATIONS

PROJECT_TITLE = 'CommonSpaces'
# PROJECT_NAME = 'mayan'
PROJECT_NAME = 'commons'
LOGIN_REDIRECT_URL = '/'

LANGUAGE_CODE = 'en-gb'
LANGUAGES = (
    ('en', _('English')),
    ('it', _('Italian')),
    ('pt', _('Portuguese')),
)

DATE_INPUT_FORMATS = ('%d-%m-%Y', '%d/%m/%Y', '%d %b %Y',)

SITE_ID = 1

WSGI_APPLICATION = 'commons.wsgi.application'
ROOT_URLCONF = 'commons.urls'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "commons", "static"),
    os.path.join(BASE_DIR, "pinax", "static"),
)

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, "commons", "templates"),
)

# --------- TEMPORARY_DIRECTORY ----------------
if os.name == 'nt':
    COMMON_TEMPORARY_DIRECTORY = os.path.join(BASE_DIR, "tmp")
else:
    COMMON_TEMPORARY_DIRECTORY = '/tmp'

# --------- Django (were redefined by Mayan) -------------------
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'commons.home'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


# --------- HIERARCHICAL GROUPS ----------------
AUTHENTICATION_BACKENDS = (
    'hierarchical_auth.backends.HierarchicalModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)

# TinyMCE settings (from roma APP of RomaPaese project)
TINYMCE_COMPRESSOR = True

TINYMCE_DEFAULT_CONFIG = {
    'width': '400', # '640',
    'height': '300', # '480',
    'plugins': 'fullscreen,media,preview,paste,table',
    'theme': 'advanced',
    'relative_urls': False,
    'theme_advanced_toolbar_location': 'top',
    'theme_advanced_toolbar_align': 'left',
    'theme_advanced_buttons1': 'undo,redo,|,formatselect,bold,italic,underline,|,' \
        'justifyleft,justifycenter,justifyright,justifyfull,|,forecolor,backcolor,' \
        'sub,sup,charmap,|,bullist,numlist,|,indent,outdent,|,link,unlink,anchor,image,media',
    'theme_advanced_buttons2': '|,tablecontrols,|,cut,copy,paste,pasteword,pastetext,selectall,|,removeformat,cleanup,|,visualaid,code,preview,fullscreen',
    'theme_advanced_buttons3': '',
    'theme_advanced_blockformats': 'p,pre,address,blockquote,h1,h2,h3,h4,' \
        'h5,h6',
    'plugin_preview_width' : '800',
    'plugin_preview_height' : '600',
    'paste_auto_cleanup_on_paste': 'true',
    }

# configure graph_models command of django-extensions
GRAPH_MODELS = {
  'all_applications': False,
  'group_models': False,
}

