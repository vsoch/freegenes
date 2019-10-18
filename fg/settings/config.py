'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''
import os

def getenv(variable_key, default=None, required=False, silent=True, boolean=False):
    ''' getenv will attempt to get an environmental variable. If the variable
        is not found, the deafult value will be returned.
        Parameters
        ==========
        variable_key: the variable name to be searched for
        required: exit with error if not found
        silent: if silent, does not print debugging information
        All credit to https://github.com/vsoch/scif/blob/master/scif/defaults.py
    '''
    variable = os.environ.get(variable_key)
    if variable is None and required:
        raise ValueError("Cannot find environment variable {}, exiting.".format(variable_key)) # replace bot

    if boolean and variable is not None:
        if not isinstance(variable, bool):
            variable = variable.lower() in ("yes", "true", "t", "1", "y")

    if not silent and variable is not None:
        print("{} found as {}".format(variable_key, variable)) # Replaced bot

    return variable

# AUTHENTICATION

# Which social auths do you want to use?
ENABLE_GLOBUS_AUTH = getenv('FG_ENABLE_GLOBUS_AUTH', default=False,boolean=True)
ENABLE_GOOGLE_AUTH = getenv('FG_ENABLE_GOOGLE_AUTH', default=False,boolean=True)
ENABLE_ORCID_AUTH = getenv('FG_ENABLE_ORCID_AUTH', default=False,boolean=True)
ENABLE_ORCID_AUTH_SANDBOX = getenv('FG_ENABLE_ORCID_AUTH_SANDBOX', default=False,boolean=True)
ENABLE_TWITTER_AUTH = getenv('FG_ENABLE_TWITTER_AUTH', default=False,boolean=True)
ENABLE_GITHUB_AUTH = getenv('FG_ENABLE_GITHUB_AUTH', default=True,boolean=True)
ENABLE_GITLAB_AUTH = getenv('FG_ENABLE_GITLAB_AUTH', default=False,boolean=True)
ENABLE_BITBUCKET_AUTH = getenv('FG_ENABLE_BITBUCKET_AUTH', default=False,boolean=True)

# NOTE you will need to set authentication methods up.
# Configuration goes into secrets.py
# See https://vsoch.github.io/freegenes/docs/development/setup#settings

# See below for additional authentication module, e.g. LDAP that are
# available, and configured, as plugins.

# Shipping (set this variable in your secrets.py
SHIPPO_TOKEN=getenv('FG_SHIPPO_TOKEN',default=None)
SHIPPO_CUSTOMER_REFERENCE=getenv('FG_SHIPPO_CUSTOMER_REFERENCE', default=None)
GOOGLE_ANALYTICS_ID=getenv('FG_GOOGLE_ANALYTICS_ID', default=None)

# SendGrid

SENDGRID_API_KEY=getenv('FG_SENDGRID_API_KEY', default=None)

# DOMAIN NAMES
## IMPORTANT: if/when you switch to https, you need to change "DOMAIN_NAME"
# to have https, otherwise some functionality will not work

DOMAIN_NAME = getenv('FG_DOMAIN_NAME', default="http://127.0.0.1")
SOCIAL_AUTH_LOGIN_REDIRECT_URL = DOMAIN_NAME

ADMINS = ((getenv('FG_ADMIN_NAME', default='vsochat'), getenv('FG_ADMIN_EMAIL', default='vsochat@gmail.com'),)
MANAGERS = ADMINS

# BioNode Parameters

HELP_CONTACT_EMAIL = getenv('FG_HELP_CONTACT_EMAIL', default='vsochat@stanford.edu')
HELP_CONTACT_PHONE = getenv('FG_HELP_CONTACT_PHONE', default=None) # "123-456-7890"
HELP_INSTITUTION_SITE = getenv('FG_HELP_INSTITUTION_SITE', default='https://srcc.stanford.edu')
NODE_INSTITUTION = getenv('FG_NODE_INSTITUTION', default='Stanford University')
NODE_URI = getenv('FG_NODE_URI', default="freegenes")
NODE_NAME = getenv('FG_NODE_NAME', default="FreeGenes")
NODE_TWITTER = getenv('FG_NODE_TWITTER', default="biobricks")

# Defaults for Physical Models

# These should be integers, will be used to generate plate locations 
# (addresses) for the well schema.
# Question: is this absolutely set in stone for the entire application? Can
# we not have more than one plate size?
DEFAULT_PLATE_HEIGHT=getenv('FG_DEFAULT_PLATE_HEIGHT', default=8)
DEFAULT_PLATE_LENGTH=('FG_DEFAULT_PLATE_LENGTH', default=16)

# Permissions and Views

## TODO: make limits here 

# DATABASE

# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': getenv('FG_DB_ENGINE', default='django.db.backends.postgresql_psycopg2'),
        'NAME': getenv('FG_DB_NAME', default='postgres'),
        'USER': getenv('FG_DB_USER', default='postgres'),
        'HOST': getenv('FG_DB_HOST', default='db'),
        'PORT': getenv('FG_DB_PORT', default='5432'),
    }
}

# Rate Limits

VIEW_RATE_LIMIT=getenv('FG_VIEW_RATE_LIMIT', default="50/1d")  # The rate limit for each view, django-ratelimit, "50 per day per ipaddress)
VIEW_RATE_LIMIT_BLOCK=getenv('FG_VIEW_RATE_LIMIT_BLOCK', default=True) # Given that someone goes over, are they blocked for the period?

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

# Map
## Default / public Mapbox token
MAPBOX_ACCESS_TOKEN = getenv('MAPBOX_ACCESS_TOKEN',default=None)
