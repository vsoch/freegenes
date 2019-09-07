'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''


from django.contrib.auth.decorators import login_required
from django.shortcuts import render 
from ratelimit.decorators import ratelimit

from fg.apps.main.models import (
    Container,
    Plate,
    PlateSet
)

from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

import os
import json


## Map

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def lab_map_view(request):
    '''the lab map view shows a map of all containers and platesets,
       which we can derive starting at the parent container. This will work
       fine for smaller labs, if a lab has thousands of containers it will
       start to run slowly and we will need a method that generates children
       on demand from the view.
    '''
    # Does the user want to jump to a container or plate?
    selection = request.GET.get('uuid')

    # Return the parent container
    nodes = {}
    max_level = 1
    for container in Container.objects.all():

        node = {"name": container.name,
                "url": container.get_absolute_url(),
                "uuid": str(container.uuid)} # used to link directly to node

        # Keep a record of the container parent uuid, if has one
        if container.parent:
            node['parent'] = str(container.parent.uuid)

        # Get the level in the tree
        level = 1
        parent = container.parent
        while parent:
            level +=1
            parent = parent.parent
           
        # Update the max nesting level
        if level > max_level:
            max_level = level

        node['level'] = level

        # If the container has plates, it's the last in a hierarchy
        children = []
        if container.plate_set.count() > 0:
            for plate in container.plate_set.all():
                children.append({"name": plate.name, 
                                 "uuid": str(plate.uuid),
                                 "url": plate.get_absolute_url()})
        node['children'] = children

        nodes[str(container.uuid)] = node
  
    # Next, append children to their parents - start at most nested
    for level in range(max_level, 0, -1): 
        for uuid, node in nodes.items():
            if node['level'] == level:
                if "parent" in node:
                    nodes[node['parent']]['children'].append(node)
                    

    # Remove all but level 1
    keepers = []
    for uuid, node in nodes.items():
        if node['level'] == 1:
            keepers.append(node)

    context = {"data": {
                  "name": "root",
                  "children": keepers},
               "selection": selection}

    return render(request, "maps/lab.html", context)


@login_required
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

    print(data)
    context = {"data": data}
    return render(request, "maps/orders.html", context)
