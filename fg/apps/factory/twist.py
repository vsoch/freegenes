'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from fg.apps.main.models import Plate
import os
import json

def get_unique_plates(rows):
    '''Use the rows from the imported csv and then present new plates to the user
       to provide, for each, a container and a name. We can derive
       that a Plate is already in the database based on the
       plate.vendor_plate_id.
    '''
    print(rows)
    plate_ids = {}

    # We need to look up all rows to populate the form
    headers = rows.pop(0)

    for row in rows:

        # The plate id maps to plate.vendor_plate_id
        plate_id = row[headers.index("Plate ID")]
        try:
            Plate.objects.get(plate_vendor_id=plate_id)

        # Only add if it doesn't exist already
        except Plate.DoesNotExist:
            if plate_id not in plate_ids:
                plate_ids[plate_id] = {"product_type": row[headers.index("Product type")],
                                       "name": row[headers.index("Name")]}

    return plate_ids
