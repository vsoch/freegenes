'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.shortcuts import render 
from django.http import Http404
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
