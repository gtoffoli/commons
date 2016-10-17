# -*- coding: utf-8 -*-"""
"""
Django settings for commons project.
"""

from django.utils.translation import ugettext_lazy as _

PRODUCTION = False
DEBUG_TOOLBAR= False
# from mayan.settings.base import *
# from base import *
XMPP_SERVER = 'openfire.commonspaces.eu'

from private import *
if PRODUCTION:
    DEBUG = False
    ALLOWED_HOSTS = ['*']
    ALLOWED_HOSTS.append(XMPP_SERVER)
else:
    DEBUG = True
    # TEMPLATE_STRING_IF_INVALID = '%s'

PROJECT_ROOT = os.path.dirname(__file__)
PARENT_ROOT = os.path.dirname(PROJECT_ROOT)

ACCOUNT_AUTHENTICATION_METHOD = "email" # "username"
ACCOUNT_USERNAME_REQUIRED = False # True
ACCOUNT_EMAIL_REQUIRED = True # False
ACCOUNT_EMAIL_VERIFICATION = "mandatory" # "optional"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True # False
SOCIALACCOUNT_EMAIL_VERIFICATION = "none" # ACCOUNT_EMAIL_VERIFICATION

ACCOUNT_ADAPTER = 'commons.adapter.MyAccountAdapter'

"""
SOCIALACCOUNT_PROVIDERS = \
    {'linkedin':
      {'SCOPE': ['r_emailaddress'],
       'PROFILE_FIELDS': ['id',
                         'first-name',
                         'last-name',
                         'email-address',
                         'picture-url',
                         'public-profile-url']}}
"""
# EMAIL_BACKEND = "mailer.backend.DbBackend"

import os
import sys

# from private import *

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    # 'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'pybb.middleware.PybbMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # 'dmuc.middleware.UserXMPPMiddleware',
)
if DEBUG and DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE_CLASSES

INSTALLED_APPS = (
    'haystack',
    # 3rd party
    'suit',
    # Django
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    # 'django.contrib.comments',
    'django_comments',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.flatpages',
    # 3rd party
    'compressor',
    # 'corsheaders',
    # 'djcelery',
    'filebrowser',
    'filetransfers',
    'mptt',
    # 'rest_framework',
    # 'rest_framework.authtoken',
    # 'solo',
    # 'south',
    # Base generic
    # 'acls',
    # 'permissions',
    # 'smart_settings',
    # 'user_management',
    # Mayan EDMS
    # 'checkouts',
    # 'document_acls',
    # 'documents',
    # 'metadata',
    # 'events',
    # extend auth model
    "hierarchical_auth",
    "django_extensions",
    "datetimewidget",
    # "django_select2",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # ... include the providers you want to enable:
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.linkedin_oauth2',
    'tinymce',
    # django-autocomplete-light
    'queryset_sequence',
    'dal',
    'dal_select2',
    'dal_queryset_sequence',
    'dal_select2_queryset_sequence',
    # from pinax project
    "pinax_theme_bootstrap",
    "bootstrapform",
    # pinax starter project ?
    # "pinax",
    # "pinax.notifications",
    "notification",
    # menus and ...
    'menu',
    'taggit',
    'taggit_labels',
    # 'taggit_live',
    'datatrans',
    # muc
    'conversejs',
    'dmuc',
    # blog
    'tagging',
    'zinnia',
    # forum
    'pybb',
    # commons project
    'viewerjs',
    # 'mailer',
    'django_messages',
    'roles',
    'django_dag',
    'commons',
    # Placed after rest_api to allow template overriding
    # Must be last on Django < 1.7 as per documentation
    # https://django-activity-stream.readthedocs.org/en/latest/installation.html
    'actstream',
    'endless_pagination',
    'djangobower',
    'django_nvd3',
	'awesome_avatar',
)
if DEBUG and DEBUG_TOOLBAR:
    INSTALLED_APPS = list(INSTALLED_APPS) + ['debug_toolbar']

BOWER_INSTALLED_APPS = (
    # 'd3#3.3.13',
    # 'nvd3#1.7.1',
    'd3#3.5.16',
    'nvd3#1.8.1',
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'DIRS': [os.path.join(BASE_DIR, "commons", "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.core.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                # theme (from pinax project)
                # "pinax_theme_bootstrap.context_processors.theme",
                # "allauth.account.context_processors.account",
                # "allauth.socialaccount.context_processors.socialaccount",
                'django_messages.context_processors.inbox',
                'zinnia.context_processors.version',  # Optional
                'pybb.context_processors.processor',
                'dmuc.context_processors.rooms',
                'commons.context_processors.processor',
            ],
        },
    },
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
    'djangobower.finders.BowerFinder',
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

# import mayan.apps
# sys.path.append(os.path.dirname(os.path.abspath(mayan.apps.__file__)))

# ========= COMMONS' CUSTOMIZATIONS

PROJECT_TITLE = 'CommonSpaces'
# PROJECT_NAME = 'mayan'
PROJECT_NAME = 'commons'
LOGIN_REDIRECT_URL = '/'
# LOGOUT_REDIRECT_URL = '/' 

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True
# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

TIME_ZONE = 'Europe/Rome'

LANGUAGE_CODE = 'en'
"""
LANGUAGES = (
    ('en', _('English')),
    ('it', _('Italian')),
    ('pt', _('Portuguese')),
)
"""
LANGUAGES = (
    ('en', 'English'),
    ('it', 'Italiano'),
    ('pt', 'Português'),
)

DATE_INPUT_FORMATS = ('%d-%m-%Y', '%d/%m/%Y', '%d %b %Y',)

SITE_ID = 1
SITE_NAME = 'CommonS Platform'

WSGI_APPLICATION = 'commons.wsgi.application'
ROOT_URLCONF = 'commons.urls'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "commons", "static"),
    os.path.join(BASE_DIR, "pinax", "static"),
)
BOWER_COMPONENTS_ROOT = os.path.join(BASE_DIR, 'components')

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
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'stream': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'errorlog': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'error.log'),
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'errorlog',],
            'level': 'ERROR',
            'propagate': True,
        },
        'dmuc': {
            'handlers': ['stream'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'filters': ['require_debug_false'],
        },
        'conversejs': {
            'handlers': ['stream'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'filters': ['require_debug_false'],
        },
        'sleekxmpp': {
            'handlers': ['stream'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'filters': ['require_debug_false'],
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
# TINYMCE_JS_URL =os.path.join(STATIC_URL, 'tinymce/tinymce.min.js')
TINYMCE_JS_URL =os.path.join(STATIC_URL, 'tinymce/js/tinymce/tinymce.min.js')
"""
TINYMCE_COMPRESSOR = True
"""

TINYMCE_DEFAULT_CONFIG = {
	'schema': "html5",
    'resize' : "both",
	'height': 350,
	# 'plugins': "advlist charmap textcolor colorpicker table link anchor image media visualblocks code fullscreen preview",
    'plugins': "advlist charmap textcolor colorpicker table link anchor image visualblocks code fullscreen preview",
	# 'toolbar': 'undo redo | formatselect bold italic underline | alignleft aligncenter alignright alignjustify | forecolor backcolor subscript superscript charmap | bullist numlist outdent indent | table link unlink anchor image media | cut copy paste removeformat | visualblocks code fullscreen preview',
    'toolbar': 'undo redo | formatselect bold italic underline | alignleft aligncenter alignright alignjustify | forecolor backcolor subscript superscript charmap | bullist numlist outdent indent | table link unlink anchor image | cut copy paste removeformat | visualblocks code fullscreen preview',
    'content_css' : os.path.join(STATIC_URL,"tinymce/mycontent.css"),
	'plugin_preview_width' : 800,
	'plugin_preview_height' : 600,
    }

FILEBROWSER_DIRECTORY = 'ugc_upload/'
FILEBROWSER_EXTENSIONS = {
# 'Image': ['.jpg','.jpeg','.gif','.png','.tif','.tiff'],
'Image': ['.jpg','.jpeg','.gif','.png'],
'Document': ['.pdf','.doc','.rtf','.txt','.xls','.csv'],
# 'Video': ['.mov','.wmv','.mpeg','.mpg','.avi','.rm'],
# 'Audio': ['.mp3','.mp4','.wav','.aiff','.midi','.m4p']
}

# configure graph_models command of django-extensions
GRAPH_MODELS = {
  'all_applications': False,
  'group_models': False,
}

TAGGIT_CASE_INSENSITIVE = True

PYBB_PERMISSION_HANDLER = 'commons.permissions.ForumPermissionHandler'
PYBB_ATTACHMENT_ENABLE = True
PYBB_SMILES = {}
PYBB_DISABLE_SUBSCRIPTIONS = True
PYBB_DISABLE_NOTIFICATIONS = True
PYBB_DEFAULT_TITLE = 'Forum'
PYBB_TOPIC_PAGE_SIZE = 20 # 10
PYBB_NICE_URL = True
# PYBB_MARKUP = 'pybb.markup.markdown.MarkdownParser'
"""!
def need_moderation(user, body):
    if user.is_full_member():
        return False
    return True
PYBB_PREMODERATION = need_moderation
"""
PYBB_PREMODERATION = False # otherwise, should customize also filter_topics and filter_posts

ZINNIA_AUTO_MODERATE_COMMENTS = False # True
ZINNIA_AUTO_CLOSE_COMMENTS_AFTER = 500 # 15 # 0 means no comments enabled at all
ZINNIA_AUTO_CLOSE_PINGBACKS_AFTER = 0 # 0 means disabling pingbacks completely
ZINNIA_AUTO_CLOSE_TRACKBACKS_AFTER = 0 # 0 means disabling trackbacks completely.

COMMONS_PROJECTS_MAX_DEPTH = 3
COMMONS_PROJECTS_NO_APPLY = ('sup',)
COMMONS_PROJECTS_NO_CHAT = ('com',)

"""
CONVERSEJS_ENABLED = True
CONVERSEJS_HIDE_MUC_SERVER = True
"""

USE_HAYSTACK = True
SEARCH_BACKEND = "whoosh"
if SEARCH_BACKEND == 'whoosh':
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
            'PATH': os.path.join(PARENT_ROOT, 'whoosh_index'),
        },
    }

# DATATRANS_CACHE_DURATION = 1
DATATRANS_TRANSLATE_MAP = {
    'flatpage': ('/admin/flatpages/flatpage/%s/', 'pk', 'title', 'commons.forms.FlatPageForm',),
    'entry': ('/admin/zinnia/entry/%s/', 'pk', 'title', 'commons.forms.BlogArticleForm',),
    'featured': ('/admin/commons/featured/%s/', 'pk', 'title', 'commons.forms.FeaturedForm',),
    'project': ('/project/%s/', 'slug', 'name', 'commons.forms.ProjectForm',),
    'repo': ('/repo/%s/', 'slug', 'name', 'commons.forms.RepoForm',),
    'oer': ('/oer/%s/', 'slug', 'title', 'commons.forms.OerForm',),
    'learningpath': ('/lp/%s/', 'slug', 'title', 'commons.forms.LpForm',),
    'pathnode': ('/pathnode/%s/', 'pk', 'label', 'commons.forms.PathNodeForm',),
}