'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.conf import settings
from fg.apps.main.models import (
    Part,
    Distribution
)

def get_unique_parts():
    '''we use this function to get parts associated with a distribution (meaning
       that they can be requested. This is different from the total parts in
       FreeGenes, which would be this query:

       Part.objects.values('gene_id').distinct().count()
    '''
    parts = set()
    for distribution in Distribution.objects.all():
        for plateset in distribution.platesets.all():
            # Each plate should be the same, so we look at the first
            plate = plateset.plates.first()          
            for well in plate.wells.all():
                parts.add(well.sample_wells.first().part.gene_id)
    return parts         


def domain_processor(request):
    return {'domain': settings.DOMAIN_NAME,
            'NODE_URI': settings.NODE_URI,
            'NODE_NAME': settings.NODE_NAME,
            'NODE_TWITTER': settings.NODE_TWITTER,  # unique parts
            'NODE_PARTS': len(get_unique_parts())}

def help_processor(request):
    return {'HELP_CONTACT_EMAIL': settings.HELP_CONTACT_EMAIL,
            'HELP_INSTITUTION_SITE': settings.HELP_INSTITUTION_SITE,
            'GOOGLE_ANALYTICS_ID': settings.GOOGLE_ANALYTICS_ID}

def auth_processor(request):
    return {"ENABLE_GLOBUS_AUTH": settings.ENABLE_GLOBUS_AUTH,
            "ENABLE_GOOGLE_AUTH": settings.ENABLE_GOOGLE_AUTH,
            "ENABLE_ORCID_AUTH": settings.ENABLE_ORCID_AUTH,
            "ENABLE_ORCID_AUTH_SANDBOX": settings.ENABLE_ORCID_AUTH_SANDBOX,
            "ENABLE_TWITTER_AUTH": settings.ENABLE_TWITTER_AUTH,
            "ENABLE_GITHUB_AUTH": settings.ENABLE_GITHUB_AUTH,
            "ENABLE_GITLAB_AUTH": settings.ENABLE_GITLAB_AUTH,
            "ENABLE_BITBUCKET_AUTH": settings.ENABLE_BITBUCKET_AUTH,
            "PLUGINS_ENABLED": settings.PLUGINS_ENABLED}
