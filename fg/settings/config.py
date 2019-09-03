'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

# AUTHENTICATION

# Which social auths do you want to use?
ENABLE_GOOGLE_AUTH = False
ENABLE_ORCID_AUTH = False
ENABLE_ORCID_AUTH_SANDBOX = False
ENABLE_TWITTER_AUTH = False
ENABLE_GITHUB_AUTH = True
ENABLE_GITLAB_AUTH = False
ENABLE_BITBUCKET_AUTH = False

# NOTE you will need to set authentication methods up.
# Configuration goes into secrets.py
# See https://vsoch.github.io/freegenes/docs/development/setup#settings

# See below for additional authentication module, e.g. LDAP that are
# available, and configured, as plugins.

# Shipping (set this variable in your secrets.py
SHIPPO_TOKEN=None

# DOMAIN NAMES
## IMPORTANT: if/when you switch to https, you need to change "DOMAIN_NAME"
# to have https, otherwise some functionality will not work (e.g., GitHub webhooks)

DOMAIN_NAME = "http://127.0.0.1"
SOCIAL_AUTH_LOGIN_REDIRECT_URL = DOMAIN_NAME
DOMAIN_NAME_HTTP = "http://127.0.0.1"
DOMAIN_NAKED = DOMAIN_NAME_HTTP.replace('http://', '')

ADMINS = (('vsochat', 'vsochat@gmail.com'),)
MANAGERS = ADMINS

# Future BioNode Parameters

HELP_CONTACT_EMAIL = 'vsochat@stanford.edu'
HELP_INSTITUTION_SITE = 'https://srcc.stanford.edu'
NODE_INSTITUTION = 'Stanford University'
NODE_URI = "srcc"
NODE_NAME = "Stanford Research Computing Center"

# Defaults for Physical Models

# These should be integers, will be used to generate plate locations 
# (addresses) for the well schema.
# Question: is this absolutely set in stone for the entire application? Can
# we not have more than one plate size?
DEFAULT_PLATE_HEIGHT=16
DEFAULT_PLATE_LENGTH=24

# Permissions and Views

## TODO: make limits here 

# DATABASE

# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'db',
        'PORT': '5432',
    }
}

# Rate Limits

VIEW_RATE_LIMIT="50/1d"  # The rate limit for each view, django-ratelimit, "50 per day per ipaddress)
VIEW_RATE_LIMIT_BLOCK=True # Given that someone goes over, are they blocked for the period?

# Plugins
# Add the name of a plugin under fg.plugins here to enable it

# Available Plugins:

# - ldap_auth: Allows sregistry to authenitcate against an LDAP directory
# - pam_auth: Allow users from (docker) host to log in
# - saml_auth: authentication with SAML

PLUGINS_ENABLED = [
#    'ldap_auth',
#    'pam_auth',
#    'saml_auth'
]
