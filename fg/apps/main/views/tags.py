'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.core.paginator import Paginator
from django.shortcuts import render 
from ratelimit.decorators import ratelimit
from django.http import Http404

from fg.apps.main.models import (
    Author,
    Collection,
    Organism,
    Part,
    Tag
)

from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

import os

def get_tag(uuid):
    '''retrieve a tag based on its uuid, if it exists. Otherwise, 404
    '''
    try:
        tag = Tag.objects.get(uuid=uuid)
        return tag
    except Tag.DoesNotExist:
        raise Http404

## Catalogs Filtered to Tags

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def tag_authors_details(request, uuid):
    tag = get_tag(uuid)
    context = {"authors": Author.objects.filter(tags=tag),
               "title": "Authors",
               "description": "Authors with Tag %s" % tag.tag}
    return render(request, "catalogs/authors.html", context=context)


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def tag_collections_details(request, uuid):
    tag = get_tag(uuid)
    context = {"collections": Collection.objects.filter(tags=tag),
               "title": "Collections",
               "description": "Collections with Tag %s" % tag.tag}
    return render(request, "catalogs/collections.html", context=context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def tag_organisms_details(request, uuid):
    tag = get_tag(uuid)
    context = {"organisms": Organism.objects.filter(tags=tag),
               "title": "Organisms",
               "description": "Organisms with tag %s" % tag.tag}
    return render(request, "catalogs/organisms.html", context=context)

def tag_parts_details(request, uuid, number_pages=50):
    '''parts are provided by a paginator.
 
       Parameters
       ==========
       number_pages: how many pages to paginate (default is 50)
    '''
    tag = get_tag(uuid)
    paginator = Paginator(Part.objects.filter(tags=tag), number_pages)
    page = request.GET.get('page')
    context = {'parts': paginator.get_page(page),
               'title': "Parts",
               'description': "Parts with tag %s" % tag.tag}
    return render(request, "catalogs/parts.html", context=context)
