"""
Django additional settings for tests and experiments.
This file must be specified explicitly in management commands.
"""
from settings import *

PRODUCTION = True
CONVERSEJS_ENABLED = True
ALLOWED_HOSTS.append(XMPP_SERVER)

