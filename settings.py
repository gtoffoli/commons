# -*- coding: utf-8 -*-"""
"""
Django settings for commons project.
"""

DEBUG_TOOLBAR= False

import os
if os.name == 'nt':
    IS_LINUX = False
else:
    IS_LINUX = True

import django
DJANGO_VERSION = django.VERSION[0]

HAS_MEETING = True
HAS_ZINNIA = True
HAS_SAML2 = True
if HAS_SAML2:
    from commons.sso_config import *
HAS_EARMASTER = True

from commons.private import *
if IS_LINUX:
    DEBUG = False
else:
    DEBUG = True
    TEMPLATE_STRING_IF_INVALID = '%s'

PROJECT_ROOT = os.path.dirname(__file__)
PARENT_ROOT = os.path.dirname(PROJECT_ROOT)

ACCOUNT_AUTHENTICATION_METHOD = "email" # "username"
ACCOUNT_USERNAME_REQUIRED = False # True
ACCOUNT_EMAIL_REQUIRED = True # False
ACCOUNT_EMAIL_VERIFICATION = "mandatory" # "optional"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True # False
SOCIALACCOUNT_EMAIL_VERIFICATION = "none" # ACCOUNT_EMAIL_VERIFICATION

ACCOUNT_ADAPTER = 'commons.adapter.MyAccountAdapter'

SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'VERSION': 'v2.12',
    },
    'linkedin_oauth2': { # added 180826
        'SCOPE': [
            'r_emailaddress',
            'r_basicprofile',
        ],
        'PROFILE_FIELDS': [
            'id',
            'first-name',
            'last-name',
            'email-address',
        ],
    },
}

# Setup caching per Django docs. In actuality, you'd probably use memcached instead of local memory.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'MAX_ENTRIES': 2000,
    }
}

# Number of seconds of inactivity before a user is marked offline
USER_ONLINE_TIMEOUT = 300
# Number of seconds that we will keep track of inactive users for before 
# their last seen is removed from the cache
USER_LASTSEEN_TIMEOUT = 60 * 60 * 24 * 7

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'commons.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'pybb.middleware.PybbMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'commons.middleware.ActiveUserMiddleware',
]

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
    'filebrowser',
    'filetransfers',
    'mptt',
    # extend auth model
    "hierarchical_auth",
    "django_extensions",
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # ... include the providers you want to enable:
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.linkedin_oauth2',
    'tinymce',
    'queryset_sequence',
    'dal',
    'dal_select2',
    'dal_queryset_sequence',
    'dal_select2_queryset_sequence',
    # "notification",
    'menu',
    'taggit',
    'taggit_labels',
    'datatrans',
    'tagging',
    'zinnia',
    'commons',
    'pybb',
    # commons project
    'viewerjs',
    'django_messages',
    'roles',
    'django_dag',
    'django_filters',
    'rest_framework',
    # Placed after rest_api to allow template overriding
    # Must be last on Django < 1.7 as per documentation
    # https://django-activity-stream.readthedocs.org/en/latest/installation.html
    'actstream',
    'djangobower',
    'django_nvd3',
    'awesome_avatar',
    'snowpenguin.django.recaptcha2',
    'brat_client',
    'django.contrib.humanize.apps.HumanizeConfig',
    # 'sekizai',
    # 'wiki',
    'xapi_client',
    #'rdflib_django',
    'el_pagination',
    'datetimewidget',
)
"""
181212 MMR DatePickerInput required Python 3.3
INSTALLED_APPS = list(INSTALLED_APPS) + ['bootstrap_datepicker_plus']
"""

if HAS_SAML2:
    INSTALLED_APPS = list(INSTALLED_APPS) + ['djangosaml2']
if HAS_EARMASTER:
    INSTALLED_APPS = list(INSTALLED_APPS) + ['earmaster']
if DEBUG and DEBUG_TOOLBAR:
    INSTALLED_APPS = list(INSTALLED_APPS) + ['debug_toolbar']

BOWER_INSTALLED_APPS = (
    # 'd3#3.3.13',
    # 'nvd3#1.7.1',
    'd3#3.5.16',
    'nvd3#1.8.1',
)

MIGRATION_MODULES = {
    'roles': None,
}

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
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                # "allauth.account.context_processors.account",
                # "allauth.socialaccount.context_processors.socialaccount",
                'django_messages.context_processors.inbox',
                'zinnia.context_processors.version',  # Optional
                'pybb.context_processors.processor',
                'commons.context_processors.processor',
                # 'sekizai.context_processors.sekizai',
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
if not IS_LINUX:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )

# --------- Pagination ----------------
PAGINATION_INVALID_PAGE_RAISES_404 = True
# ---------- Search ------------------
SEARCH_SHOW_OBJECT_TYPE = False
# ---------- Django REST framework -----------
"""
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
"""
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

# ========= COMMONS' CUSTOMIZATIONS

PROJECT_TITLE = 'CommonSpaces'
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
LANGUAGES = [
    (u'en', u'English'),
    (u'hr', u'Hrvatski'),
    (u'it', u'Italiano'),
    (u'pt', u'Português'),
    (u'ru', u'Русский'),
]
if not IS_LINUX:
    LANGUAGES = LANGUAGES+[(u'ar', u'Arabic')]
LANGUAGES_DICT = dict(LANGUAGES)
RTL_LANGUAGES = ['ar']

DATE_INPUT_FORMATS = ('%d-%m-%Y', '%d/%m/%Y', '%d %b %Y',)

SITE_ID = 1
SITE_NAME = 'CommonSpaces'

WSGI_APPLICATION = 'commons.wsgi.application'
ROOT_URLCONF = 'commons.urls'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

if IS_LINUX:
    SCORM_URL = '/scorm/'
    SCORM_ROOT = os.path.join(BASE_DIR, 'scorm')
else:
    SCORM_URL = '/media/scorm/'
    SCORM_ROOT = os.path.join(MEDIA_ROOT, 'scorm') 
SCORM_EXPIRATION = 60 * 60 * 24

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

BOWER_COMPONENTS_ROOT = os.path.join(BASE_DIR, 'components')

# --------- TEMPORARY_DIRECTORY ----------------
if os.name == 'nt':
    COMMON_TEMPORARY_DIRECTORY = os.path.join(BASE_DIR, "tmp")
else:
    COMMON_TEMPORARY_DIRECTORY = '/tmp'

# ----------------------------
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
    }
}

# --------- HIERARCHICAL GROUPS ----------------
AUTHENTICATION_BACKENDS = (
    'hierarchical_auth.backends.HierarchicalModelBackend',
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
)
if HAS_SAML2:
    AUTHENTICATION_BACKENDS = list(AUTHENTICATION_BACKENDS) + ['djangosaml2.backends.Saml2Backend']

TINYMCE_DEFAULT_CONFIG = {
    'schema': "html5",
    'resize' : "both",
    'height': 350,
    'branding': False,
    # 'plugins': "advlist charmap textcolor colorpicker table link anchor image media visualblocks code fullscreen preview",
    'plugins': "paste lists advlist charmap textcolor colorpicker table link anchor image visualblocks code fullscreen preview",
    # 'toolbar': 'undo redo | formatselect bold italic underline | alignleft aligncenter alignright alignjustify | forecolor backcolor subscript superscript charmap | bullist numlist outdent indent | table link unlink anchor image media | cut copy paste removeformat | visualblocks code fullscreen preview',
    'toolbar': 'undo redo | formatselect styleselect bold italic underline | alignleft aligncenter alignright alignjustify | forecolor backcolor subscript superscript charmap | bullist numlist outdent indent | table link unlink anchor image | cut copy paste removeformat | visualblocks code fullscreen preview',
    'content_css' : os.path.join(STATIC_URL,"tinymce/mycontent.css"),
    'style_formats': [
      {'title': '10px', 'inline': 'span', 'styles': {'font-size': '10px'}},
      {'title': '11px', 'inline': 'span', 'styles': {'font-size': '11px'}},
      {'title': '12px', 'inline': 'span', 'styles': {'font-size': '12px'}},
      {'title': '13px', 'inline': 'span', 'styles': {'font-size': '13px'}},
      {'title': '14px', 'inline': 'span', 'styles': {'font-size': '14px'}},
      {'title': '15px', 'inline': 'span', 'styles': {'font-size': '15px'}},
      {'title': '16px', 'inline': 'span', 'styles': {'font-size': '16px'}},
      {'title': '17px', 'inline': 'span', 'styles': {'font-size': '17px'}},
      {'title': '18px', 'inline': 'span', 'styles': {'font-size': '18px'}},
      {'title': 'clear floats', 'block': 'div', 'styles': {'clear': 'both'}},
    ],
    'plugin_preview_width' : 800,
    'plugin_preview_height' : 600,
    'advlist_class_list' : [
        {'title': 'select', 'value': ''},
        {'title': 'image responsive', 'value': 'img-responsive-basic center-block'},
        {'title': 'image responsive left', 'value': 'img-responsive-basic pull-left'},
        {'title': 'image responsive right', 'value': 'img-responsive-basic pull-right'}],
    'image_advtab' : True,
    'image_caption': False,
    'image_class_list' : [
        {'title': 'select', 'value': ''},
        {'title': 'image responsive', 'value': 'img-responsive-basic center-block'},
        {'title': 'image responsive left', 'value': 'img-responsive-basic pull-left marginR10'},
        {'title': 'image responsive right', 'value': 'img-responsive-basic pull-right marginL10'}],
    'paste_data_images': True,
    'table_class_list': [
        {'title': 'select', 'value': ''},
        {'title': 'table responsive', 'value': 'table-responsive'},
        {'title': 'table responsive width 100%', 'value': 'table-responsive width-full'},],
    'file_browser_callback_types': 'image',
    'paste_as_text': True,
    # URL settings
    # 'convert_urls' : False,
    'relative_urls' : False,
}

FILEBROWSER_DIRECTORY = 'ugc_upload/'
FILEBROWSER_EXTENSIONS = {
# 'Image': ['.jpg','.jpeg','.gif','.png','.tif','.tiff'],
'Image': ['.jpg','.jpeg','.gif','.png'],
# 'Document': ['.pdf','.doc','.rtf','.txt','.xls','.csv'],
# 'Video': ['.mov','.wmv','.mpeg','.mpg','.avi','.rm'],
# 'Audio': ['.mp3','.mp4','.wav','.aiff','.midi','.m4p']
}
FILEBROWSER_MAX_UPLOAD_SIZE = '2097152'

# configure graph_models command of django-extensions
GRAPH_MODELS = {
  'all_applications': False,
  'group_models': False,
}

TAGGIT_CASE_INSENSITIVE = True

# configure django_messages
DJANGO_MESSAGES_NOTIFY = True # True is also the default value
DJANGO_MESSAGES_NOTIFY_BY_USER = True # if True, personal preference is given by user through the get_email_notifications method
try:
    DEFAULT_HTTP_PROTOCOL = PROTOCOL # PROTOCOL can be set in private.py
except:
    pass

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

ZINNIA_AUTO_MODERATE_COMMENTS = True # True means that comments are marked as non public
ZINNIA_AUTO_CLOSE_COMMENTS_AFTER = 0 # 0 means no comments enabled at all
ZINNIA_AUTO_CLOSE_PINGBACKS_AFTER = 0 # 0 means disabling pingbacks completely
ZINNIA_AUTO_CLOSE_TRACKBACKS_AFTER = 0 # 0 means disabling trackbacks completely.

"""
WIKI_ACCOUNT_HANDLING = False # True
WIKI_ANONYMOUS_WRITE = False # True
"""

COMMONS_COMMUNITIES_MAX_DEPTH = 2
COMMONS_PROJECTS_MAX_DEPTH = 2
COMMONS_PROJECTS_NO_APPLY = ('sup',)
COMMONS_PROJECTS_NO_CHAT = ('com',)

USE_HAYSTACK = True
SEARCH_BACKEND = "whoosh"
if SEARCH_BACKEND == 'whoosh':
    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
            'PATH': os.path.join(PARENT_ROOT, 'whoosh_index'),
        },
    }

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_FILTER_BACKENDS': ('django_filters.rest_framework.DjangoFilterBackend',)
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

HOMEPAGE_TIMEOUT = 60 * 60 * 24 # 1 day

#file attachment
EXTS_FILE_ATTACHMENT = 'txt|doc|docx|ppt|pptx|pdf|xls|xlsx|odt|odp|ods|jpg|png|mp3|mp4|rtf|ipynb|zip'
SIZE_FILE_ATTACHMENT = 10
EXTS_FILE_USER_PROFILE = 'pdf'
SIZE_FILE_USER_PROFILE = 2
PLUS_SIZE = 4
SUB_EXTS = 'zip'

XAPI_VOCABULARIES_MODULE = None
XAPI_DEFAULT_PLATFORM = 'CommonS Platform'
XAPI_DEFAULT_RECIPES = ['Events']
XAPI_ACTIVITY_ALIASES = {
    'UserProfile': 'user profile',
    'Folder': 'folder',
    'FolderDocument': 'document',
    'Project': 'project',
    'ProjectMember': 'membership',
    'Forum': 'discussion forum',
    'Topic': 'discussion topic',
    'Post': 'forum post',
    'Repo': 'resource repository',
    'OER': 'oer',
    'OerEvaluation': 'oer rating',
    'LearningPath': 'learning path',
    'PathNode': 'learning unit',
    'Entry': 'article',
    'Message': 'private message',
    'Webpage': 'web page',
    'OnlineMeeting': 'meeting',
}
XAPI_VERB_ALIASES = {
    'Accept': 'accepted',
    'Access': 'accessed',
    'Approve': 'approved',
    'Bookmark': 'bookmarked',
    'Create': 'created',
    'Delete': 'deleted',
    'Edit': 'edited',
    'Play': 'played',
    'Reject': 'rejected',
    'Search': 'searched',
    'Send': 'sent',
    'Submit': 'submitted',
    'View': 'viewed',
}

