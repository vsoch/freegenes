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
from fg.apps.orders.views.shipping import update_shippo_transactions


class Command(BaseCommand):
    '''Update tracking using the Shippo API
    '''

    def handle(self, *args, **options):
        count_updated = update_shippo_transactions()
        print("Tracking updated for %s orders." % count_updated)
