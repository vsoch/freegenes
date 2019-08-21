'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.core.management.base import (
    BaseCommand,
    CommandError
)

from fg.apps.users.models import User

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    '''add staff will add admin and manager privledges to freegenes. 
       The super user is an admin that can access the administrative
       interface, and pretty much do anything.
    '''
    def add_arguments(self, parser):
        parser.add_argument(dest='username', nargs=1, type=str)

    help = "Generates an admin for freegenes."
    def handle(self, *args, **options):
        if options['username'] is None:
            raise CommandError("Please provide a username with --username")

        logger.debug("Username: %s" % options['username']) 
        try:
            user = User.objects.get(username=options['username'][0])
        except User.DoesNotExist:
            raise CommandError("This username does not exist.")

        if user.is_staff is True:
            raise CommandError("This user is already staff")        
        else:
            user = User.objects.add_staff(user)
            print("%s is now FreeGenes staff." %(user.username))
