"""
Django settings for commons project.
"""

from mayan.settings.base import *

# ========= EXTENSIONS BY COMMONS

INSTALLED_APPS = list(INSTALLED_APPS) + [
    # extend auth model
    "hierarchical_auth",
    "django_extensions",
    # "organizations",
    # theme (from pinax project)
    "pinax_theme_bootstrap",
    "bootstrapform",
    # pinax starter project ?
    "pinax",
    # commons project
    'commons',
]

TEMPLATE_CONTEXT_PROCESSORS = list(TEMPLATE_CONTEXT_PROCESSORS) + [
    # theme (from pinax project)
    "pinax_theme_bootstrap.context_processors.theme",
]


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

from private import *

# --------- HIERARCHICAL GROUPS ----------------
AUTHENTICATION_BACKENDS = (
    'hierarchical_auth.backends.HierarchicalModelBackend',
)
