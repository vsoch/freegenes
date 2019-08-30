'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render 
from django.http import Http404, HttpResponse
from ratelimit.decorators import ratelimit

from fg.apps.orders.models import Order
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

import os

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

## Catalogs with Pagination (too large for table)

def catalog_pagination(request, Model, label, number_pages=50):
    '''a shared function to provide generic pagination, and return a template.
 
       Parameters
       ==========
       request: the request object from the receiving view
       Model: the Model class to use
       label: the label, e.g., "samples" expected under catalogs/<label>.html
              along with the variable to provide in the page.
       number_pages: how many pages to paginate (default is 50)
    '''
    paginator = Paginator(Model.objects.all(), number_pages)
    page = request.GET.get('page')
    context = {label: paginator.get_page(page)}
    template = "catalogs/%s.html" % label
    return render(request, template, context=context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def samples_catalog_view(request):
    return catalog_pagination(request, Sample, "samples")

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def parts_catalog_view(request):
    return catalog_pagination(request, Part, "parts")

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def plates_catalog_view(request):
    return catalog_pagination(request, Plate, "plates")


## Download and Export

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def download_mta(request, uuid):
    '''download an MTA from the server, only available to admin and staff.
       The uuid is for an order, since we render the link from the order page.
    '''

    # Staff or admin is required to download, as MTA isn't exposed via URL
    if request.user.is_staff or request.user.is_superuser:

        # Do we find the associated order?
        try:
            order = Order.objects.get(uuid=uuid)
        except Order.DoesNotExist:
            raise Http404

        # Stream the file to download if the mta exists
        if order.material_transfer_agreement:
            file_path = order.material_transfer_agreement.agreement_file.path
            if os.path.exists(file_path):
                _, ext = os.path.splitext(file_path)
                with open(file_path, 'rb') as fh:
                    response = HttpResponse(fh.read(), content_type="application/%s" % ext.strip('.'))
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
                return response

        # No MTA for this order
        messages.warning(request, "That order doesn't have a material transfer agreement.")

    raise Http404


def generate_plates_csv(


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def download_plateset_csv(request, uuid):
    '''download a csv file for a plateset.
    '''
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'

    writer = csv.writer(response)
    writer.writerow(['First row', 'Foo', 'Bar', 'Baz'])
    writer.writerow(['Second row', 'A', 'B', 'C', '"Testing"', "Here's a quote"])

    return response


Plate name, Plate type, Well Address, Part name, Part gene_id, Sample evidence, Part sequence
