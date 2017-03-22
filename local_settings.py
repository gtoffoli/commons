"""
Django additional settings for tests and experiments.
This file must be specified explicitly in management commands.
"""
from settings import *

CONVERSEJS_ENABLED = True
ALLOWED_HOSTS.append(XMPP_SERVER)

