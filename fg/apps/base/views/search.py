'''

Copyright (C) 2017-2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.db.models import Q
from django.shortcuts import render
from ratelimit.decorators import ratelimit

from fg.apps.main.models.queries import get_part_available_query
from fg.apps.base.context_processors import get_unique_parts
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


# Parts Search #################################################################

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def parts_search_view(request, query=None):
    '''search only parts. We expose this to the user on the main pages (and
       hide the other search interfaces for admin or similar) as the user is
       primarily interested in parts. See 
       https://github.com/vsoch/freegenes/issues/139
    '''
    context = {'submit_result': 'anything'}

    # First go, see if the user added a query variable as a GET request
    if query is None:
        query = request.GET.get('q')
 
    query_type = request.GET.get('type')

    # True returns only available parts, False all parts
    available = request.GET.get('availableParts', False)

    # Empty query should return all parts ("")
    if query is not None:
        results = parts_query(query, available)
        context["results"] = results
 
    return render(request, 'search/parts_search.html', context)


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def run_parts_search(request):
    '''The driver to show results for a parts search.
    '''
     
    if request.method == 'POST':
        q = request.POST.get('q')
        availableBox = request.POST.get('availableParts', "false")
    else:
        q = request.GET.get('q')
        availableBox = request.GET.get('availableParts', "false")

    available = True
    if availableBox == "false":
        available = False
    
    if q is not None:    
        results = parts_query(q, available)
        context = {"results": results,
                   "submit_result": "anything"}
        return render(request, 'search/parts_result.html', context)


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
 
    query_type = request.GET.get('type')

    if query is not None:
        results = freegenes_query(query, query_type, request=request)
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
        results = freegenes_query(q, request=request)
        context = {"results": results,
                   "submit_result": "anything"}
        return render(request, 'search/result.html', context)


# Search Function ##############################################################

def parts_query(q, available=False):
    '''search only across parts - we provide this search endpoint on the parts
       catalog page. If available is True, return only available parts.
    '''
    if q in ["all", ""]:
        parts = Part.objects.all()
    else:

        # If the user adds hashtag, remove
        if q.startswith("#"):
            q = q.replace("#", '', 1)

        parts = Part.objects.filter(
                        Q(name__icontains=q) |
                        Q(tags__tag__icontains=q) |
                        Q(description__icontains=q) |
                        Q(part_type__icontains=q) |
                        Q(gene_id__icontains=q)).distinct()

    # Generate list of available to annotate
    gene_ids = list(get_unique_parts())
    query = get_part_available_query(gene_ids)
    available_uuids = [str(p.uuid) for p in Part.objects.raw(query)[:]]

    if available:
        parts = parts.filter(uuid__in=available_uuids)

    # Need to annotate parts
    for part in parts:
        part.is_available = False
        if str(part.uuid) in available_uuids:
            part.is_available = True

    return parts


def distributions_query(q):
    '''specific search for distributions
    '''
    return Distribution.objects.filter(
                    Q(name__icontains=q) |
                    Q(description__icontains=q)).distinct()


def containers_query(q):
    '''specific search for containers
    '''
    return Container.objects.filter(
                    Q(name__icontains=q) |
                    Q(container_type__icontains=q) |
                    Q(description__icontains=q)).distinct()


def organisms_query(q):
    '''specific search for organisms
    '''
    return Organism.objects.filter(
                    Q(name__icontains=q) |
                    Q(tags__tag__icontains=q) |
                    Q(description__icontains=q)).distinct()


def collections_query(q):
    '''specific search for collections
    '''
    return Collection.objects.filter(Q(name__icontains=q) |
                                     Q(tags__tag__icontains=q)).distinct()


def institutions_query(q):
    '''specific search for institutions
    '''
    return Institution.objects.filter(
                    Q(name__icontains=q)).distinct()
    

def modules_query(q):
    '''specific search for modules
    '''
    return Module.objects.filter(
                    Q(name__icontains=q) |
                    Q(model_id__icontains=q) |
                    Q(module_type__icontains=q)).distinct()

def plates_query(q):
    '''specific search for plates
    '''
    return Plate.objects.filter(
                    Q(name__icontains=q) |
                    Q(plate_type__icontains=q) |
                    Q(status__icontains=q) |
                    Q(thaw_count__icontains=q) |
                    Q(plate_form__icontains=q)).distinct()

def samples_query(q):
    '''specific search for samples
    '''
    return Sample.objects.filter(
                    Q(evidence__icontains=q) |
                    Q(sample_type__icontains=q) |
                    Q(vendor__icontains=q) |
                    Q(status__icontains=q)).distinct()


def tags_query(q):
    '''specific search for modules
    '''
    return Tag.objects.filter(
                    Q(tag__icontains=q)).distinct()


def freegenes_query(q, query_types=None, request=None):
    '''for a general freegenes query, we might be looking for a container,
       collection, plate, or other entity not associated with a person/order
       We do search over institutions in case the user is looking for an 
       associated part. If a request object is provided, we check if
       the user is authenticated. If so, we remove search for parts,
       plates, tags, and organisms.
    '''
    searches = {'containers': containers_query,
                'collections': collections_query,
                'distributions': distributions_query,
                'institutions': institutions_query,
                'modules': modules_query,
                'organisms': organisms_query,
                'samples': samples_query,
                'parts': parts_query,
                'plates': plates_query,
                'tags': tags_query}

    # If the user doesn't provide one or more types, search all
    if not query_types:
        query_types = list(searches.keys())
    else:
        query_types = query_types.split(",")

    skips = []
    # If a request is provided, check if the user is admin/staff
    if request is not None:
        if not request.user.is_staff and not request.user.is_superuser:
            skips = ['parts', 'plates', 'tags', 'organisms', 'containers', 'institutions']

    results = [] 
    for query_type in query_types:
        if query_type in searches and query_type not in skips:
            results = list(chain(results, searches[query_type](q)))

    return results
