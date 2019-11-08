'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''


from django.shortcuts import render 
from ratelimit.decorators import ratelimit

from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block,
    MAPBOX_ACCESS_TOKEN as mapbox_token
)

import os
import json

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def order_map_view(request):
    '''A nightly job gets updated latitudes and longitudes from the shippo API,
       render them here. The order coordinates are saved to /code/data/ordercoords.json
    '''
    data = []
 
    order_coords = "/code/data/ordercoords.json"
    if os.path.exists(order_coords):
        with open(order_coords, 'r') as filey:
            data = json.loads(filey.read())

    context = { "data": data, "mapbox_token": mapbox_token }

    return render(request, "maps/orders.html", context)
