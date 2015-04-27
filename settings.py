"""
Django settings for commons project.
"""

PRODUCTION = False
from mayan.settings.base import *
from private import *

if PRODUCTION:
    DEBUG = False
    ALLOWED_HOSTS = ['*']
else:
    DEBUG = True
    TEMPLATE_STRING_IF_INVALID = '%s'

# ========= EXTENSIONS BY COMMONS

MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES.extend((
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
))

INSTALLED_APPS = list(INSTALLED_APPS) + [
    'django.contrib.flatpages',
    # extend auth model
    "hierarchical_auth",
    "django_extensions",
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
    # commons project
    'commons',
]

TEMPLATE_CONTEXT_PROCESSORS = list(TEMPLATE_CONTEXT_PROCESSORS) + [
    # theme (from pinax project)
    "pinax_theme_bootstrap.context_processors.theme",
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
]

# in development, disable template caching
# if os.name == 'nt':
if not PRODUCTION:
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )


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

# --------- OpenPGP signature ----------------
if os.name == 'nt':
    SIGNATURES_GPG_PATH = '\\Program Files (x86)\\GNU\\GnuPG\\pub\\gpg.exe'
else:
    SIGNATURES_GPG_PATH = '/usr/bin/gpg'

# --------- OCR ----------------
if os.name == 'nt':
    OCR_TESSERACT_PATH = '/Program Files (x86)/Tesseract-OCR/tesseract.exe'
    OCR_UNPAPER_PATH = '/Program Files (x86)/PDFRead/bin/unpaper.exe'
    OCR_PDFTOTEXT_PATH = '/Program Files (x86)/xpdf/pdftotext.exe'
else:
    OCR_TESSERACT_PATH = '/usr/bin/tesseract'
    OCR_UNPAPER_PATH = '/usr/bin/unpaper'
    OCR_PDFTOTEXT_PATH = '/usr/bin/pdftotext'

# ========= DON'T KNOW WHY THIS NEEDED

import mayan.apps
sys.path.append(os.path.dirname(os.path.abspath(mayan.apps.__file__)))

# ========= COMMONS' CUSTOMIZATIONS

from django.utils.translation import ugettext_lazy as _

PROJECT_TITLE = 'CommonSpaces'
# PROJECT_NAME = 'mayan'
PROJECT_NAME = 'commons'
LOGIN_REDIRECT_URL = '/'

LANGUAGE_CODE = 'en-gb'
LANGUAGES = (
    ('en', _('English')),
)

WSGI_APPLICATION = 'commons.wsgi.application'
ROOT_URLCONF = 'commons.urls'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
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
)

# --------- EXCEPTIONS TO THE MAYAN'S "LOGIN REQUIRED" GENERAL RULE ----------------
LOGIN_EXEMPT_URLS = list(LOGIN_EXEMPT_URLS) + [
    r'^$',
    r'^accounts/',
    r'^info/',
    r"^cops/$",
    r"^project/(?P<project_slug>[\w-]+)/$",
    r"^repos/$",
    r"^repo/(?P<repo_slug>[\w-]+)/$",
]

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

