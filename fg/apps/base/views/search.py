'''

Copyright (C) 2017-2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.db.models import Q
from django.shortcuts import render
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
    Order,
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


# Search Pages #################################################################

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def search_view(request):
    context = {'active':'share'}
    return render(request, 'search/search.html', context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def search_query(request, query=None):
    '''query is a post, and results returned immediately'''
    context = {'submit_result':'anything'}
    if query is not None:
        results = freegenes_query(query)
        context["results"] = results
 
    return render(request, 'search/search_single_page.html', context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def run_search(request):
    '''container_search is the ajax driver to show results for a container search.
    by default we search container collection name.
    ''' 
    if request.is_ajax():
        q = request.GET.get('q')
        if q is not None:    
            results = freegenes_query(q)
            context = {"results": results,
                       "submit_result": "anything"}

            return render(request, 'search/result.html', context)


# Search Function ##############################################################

def freegenes_query(q):
    return Collection.objects.filter(
                Q(name__contains=q) |
                Q(containers__name__contains=q) |
                Q(containers__tags__name__contains=q) |
                Q(containers__tag__contains=q)).distinct()
