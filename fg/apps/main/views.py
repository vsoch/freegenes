'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render 
from django.http import Http404
from ratelimit.decorators import ratelimit

from fg.apps.main.models import (
    Author,
    Container,
    Collection,
    Distribution,
    Institution,
    Module,
    Operation,
    Organism,
    Part,
    Plan,
    Plate,
    PlateSet,
    Protocol,
    Robot,
    Sample,
    Schema,
    Tag
)

from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

## Detail Pages

def get_instance(request, uuid, Model):
    '''a helper to get an instance of a particular type based on its uuid. If
       we find the instance, we return it's details page. If not, 
       we return a 404.
    '''
    try:
        instance = Model.objects.get(uuid=uuid)
        template = 'details/%s_details.html' % instance.get_label()
        return render(request, template, context={'instance': instance})
    except Model.DoesNotExist:
        raise Http404

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def author_details(request, uuid):
    # might require admin/staff (or customize in view)
    return get_instance(request, uuid, Author)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def container_details(request, uuid):
    return get_instance(request, uuid, Container)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def collection_details(request, uuid):
    return get_instance(request, uuid, Collection)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def distribution_details(request, uuid):
    # will require admin/staff
    return get_instance(request, uuid, Distribution)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def institution_details(request, uuid):
    return get_instance(request, uuid, Institution)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def module_details(request, uuid):
    return get_instance(request, uuid, Module)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def operation_details(request, uuid):
    # likely will require admin/staff
    return get_instance(request, uuid, Operation)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def organism_details(request, uuid):
    return get_instance(request, uuid, Organism)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def part_details(request, uuid):
    return get_instance(request, uuid, Part)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def plan_details(request, uuid):
    return get_instance(request, uuid, Plan)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def plate_details(request, uuid):
    return get_instance(request, uuid, Plate)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def plateset_details(request, uuid):
    return get_instance(request, uuid, PlateSet)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def protocol_details(request, uuid):
    return get_instance(request, uuid, Protocol)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def robot_details(request, uuid):
    return get_instance(request, uuid, Robot)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def sample_details(request, uuid):
    return get_instance(request, uuid, Sample)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def schema_details(request, uuid):
    return get_instance(request, uuid, Schema)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def tag_details(request, uuid):
    return get_instance(request, uuid, Tag)

## Map

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def lab_map_view(request):
    '''the lab map view shows a map of all containers and platesets,
       which we can derive starting at the parent container. This will work
       fine for smaller labs, if a lab has thousands of containers it will
       start to run slowly and we will need a method that generates children
       on demand from the view.
    '''
    # Return the parent container
    nodes = {}
    max_level = 1
    for container in Container.objects.all():

        node = {}
        node['name'] = container.name
        node['url'] = container.get_absolute_url()

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
                children.append({"name": plate.name, "url": plate.get_absolute_url()})
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

    root = {"name": "root",
            "children": keepers}

    return render(request, "maps/lab.html", {"data": root})


## Catalogs

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def catalog_view(request):
    return render(request, "catalogs/catalog.html")

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def collections_catalog_view(request):
    context = {"collections": Collection.objects.all()}
    return render(request, "catalogs/collections.html", context=context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def platesets_catalog_view(request):
    context = {"platesets": PlateSet.objects.all()}
    return render(request, "catalogs/platesets.html", context=context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def distributions_catalog_view(request):
    context = {"distributions": Distribution.objects.all()}
    return render(request, "catalogs/distributions.html", context=context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def tags_catalog_view(request, selection=None):
    '''if selection is defined, the user wants to jump directly to one of
       the tabbed sections.
    '''
    context = {"tags": Tag.objects.all(), 
              "selection": selection}
    return render(request, "catalogs/tags.html", context=context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def parts_catalog_view(request):
    paginator = Paginator(Part.objects.all(), 50)
    page = request.GET.get('page')
    context = {"parts": paginator.get_page(page)}
    return render(request, "catalogs/parts.html", context=context)
