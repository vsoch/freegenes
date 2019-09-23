'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from freegenes.client.twist import Client

from fg.settings import (
    FREEGENES_TWIST_TOKEN,
    FREEGENES_TWIST_EUTOKEN,
    FREEGENES_TWIST_EMAIL
)

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
