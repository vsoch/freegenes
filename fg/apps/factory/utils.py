'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.core.cache import caches
from freegenes.client.twist import Client
from fg.apps.main.models import Plate

from fg.settings import CACHES

from io import StringIO
import json
import csv


def read_csv(fileobj, delim):
    '''read the file object (a csv) into the file.
    '''
    csv_file = StringIO(fileobj.read().decode())
    reader = csv.reader(csv_file, delimiter=delim)
    rows = []
    for row in reader:
        rows.append(row)
    fileobj.close()
    return rows


def get_client():
    '''use the parameters for the Twist tokens to create a client. If it's
       not possible, return None
    '''
    client = None
    if not FREEGENES_TWIST_TOKEN or not FREEGENES_TWIST_EUTOKEN:
        return client

    client = Client(token=FREEGENES_TWIST_TOKEN,
                    eutoken=FREEGENES_TWIST_EUTOKEN,
                    email=FREEGENES_TWIST_EMAIL)
   
    # If the client didn't provide an email, get it
    if not client.email:
        client.whoami()
    return client


def get_orders():
    '''get orders from the Twist API - this function relies on the twist
       token, end user token, and email being defined in settings/config.py
    '''
    client = get_client()
    orders = []

    if not client:
        return orders
    return client.orders()


def get_unique_plates(order_id):
    '''Based on an order_id (the sfdc_id in Twist) retrieve the rows
       from the PlatesetMap, and then present new plates to the user
       to provide, for each, a container and a name. We can derive
       that a Plate is already in the database based on the
       plate.vendor_plate_id. *important* This function takes a bit
       to run, so the best we can do is show the user a spinner while
       waiting. If possible, we might want to cache the rows response
       somewhere in the future.
    '''
    # First try looking up in cache
    cache_name = list(CACHES.keys())[0] # default
    cache_key = 'twist_order_platemaps_%s' % order_id
    print("Cache key for plate ids is %s" % cache_key)
    cache = caches[cache_name]

    # Check if the order already is cached
    plate_ids = cache.get(cache_key, dict())

    # We need to load json back into list of lists
    if plate_ids:
        plate_ids = json.loads(plate_ids)

    client = get_client()

    # If we don't have a client, or we do have plate ids, return
    if not client or plate_ids:
        return plate_ids

    # We need to look up all rows to populate the form
    rows = client.order_platemaps(sfdc_id=order_id)
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

    # Save to cache (10 minutes)
    cache.set(cache_key, json.dumps(plate_ids), 600)

    return plate_ids
