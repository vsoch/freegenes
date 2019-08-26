'''

Copyright (C) 2017-2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.db.models import Q
from django.shortcuts import render
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

from itertools import chain

# General Search ###############################################################

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def search_view(request, query=None):
    '''this is the base search view if the user goes to the page 
       without having made a query, or having given a term
       to the url.
    '''
    context = {'submit_result': 'anything'}

    # First go, see if the user added a query variable as a GET request
    if query is None:
        query = request.GET.get('q')
 
    query_type=request.GET.get('type')

    if query is not None:
        results = freegenes_query(query, query_type)
        context["results"] = results 
    return render(request, 'search/search.html', context)


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def run_search(request):
    '''The driver to show results for a general search.
    ''' 
    if request.method == 'POST':
        q = request.POST.get('q')
    else:
        q = request.GET.get('q')

    if q is not None:    
        results = freegenes_query(q)
        context = {"results": results,
                   "submit_result": "anything"}
        return render(request, 'search/result.html', context)


# Search Function ##############################################################

def parts_query(q):
    '''search only across parts - we provide this search endpoint on the parts
       catalog page.
    '''
    return Part.objects.filter(
                    Q(name__contains=q) |
                    Q(description__contains=q) |
                    Q(part_type__contains=q) |
                    Q(gene_id__contains=q)).distinct()


def containers_query(q):
    '''specific search for containers
    '''
    return Container.objects.filter(
                    Q(name__contains=q) |
                    Q(container_type__contains=q) |
                    Q(description__contains=q)).distinct()


def organisms_query(q):
    '''specific search for organisms
    '''
    return Organism.objects.filter(
                    Q(name__contains=q) |
                    Q(description__contains=q)).distinct()


def collections_query(q):
    '''specific search for collections
    '''
    return Collection.objects.filter(Q(name__contains=q)).distinct()


def institutions_query(q):
    '''specific search for institutions
    '''
    return Institution.objects.filter(
                    Q(name__contains=q)).distinct()
    

def modules_query(q):
    '''specific search for modules
    '''
    return Module.objects.filter(
                    Q(name__contains=q) |
                    Q(model_id__contains=q) |
                    Q(module_type__contains=q)).distinct()

def tags_query(q):
    '''specific search for modules
    '''
    return Tag.objects.filter(
                    Q(tag__contains=q)).distinct()


def freegenes_query(q, query_types=None):
    '''for a general freegenes query, we might be looking for a container,
       collection, plate, or other entity not associated with a person/order
       We do search over institutions in case the user is looking for an 
       associated part.
    '''
    searches = {'containers': containers_query,
                'collections': collections_query,
                'institutions': institutions_query,
                'modules': modules_query,
                'organisms': organisms_query,
                'parts': parts_query,
                'tags': tags_query}

    # If the user doesn't provide one or more types, search all
    if not query_types:
        query_types = list(searches.keys())
    else:
        query_types = query_types.split(",")

    results = [] 
    for query_type in query_types:
        if query_type in searches:
            results = list(chain(results, searches[query_type](q)))

    return results
