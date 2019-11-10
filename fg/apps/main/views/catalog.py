'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.core.paginator import Paginator
from django.shortcuts import render 
from django.http import Http404
from ratelimit.decorators import ratelimit

from fg.apps.main.models import (
    Container,
    Collection,
    Distribution,
    Organism,
    Part,
    Plate,
    PlateSet,
    Sample,
    Tag
)

from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

import os

## Catalogs

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def catalog_view(request):
    return render(request, "catalogs/catalog.html")

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def collections_catalog_view(request):
    context = {"collections": Collection.objects.all()}
    return render(request, "catalogs/collections.html", context=context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def containers_catalog_view(request):
    context = {"containers": Container.objects.all()}
    return render(request, "catalogs/containers.html", context=context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def organisms_catalog_view(request):
    context = {"organisms": Organism.objects.all()}
    return render(request, "catalogs/organisms.html", context=context)

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

def catalog_pagination(request, queryset, label, number_pages=50, title=None):
    '''a shared function to provide generic pagination, and return a template.
 
       Parameters
       ==========
       request: the request object from the receiving view
       queryset: the queryset to use (should be ordered)
       label: the label, e.g., "samples" expected under catalogs/<label>.html
              along with the variable to provide in the page.
       number_pages: how many pages to paginate (default is 50)
    '''
    paginator = Paginator(queryset, number_pages)
    page = request.GET.get('page')
    context = {label: paginator.get_page(page), "title": title}
    template = "catalogs/%s.html" % label
    return render(request, template, context=context)


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def distribution_parts(request, uuid):
    '''show the unique parts associated with a specific distribution.
    '''
    try:
        distribution = Distribution.objects.get(uuid=uuid)
    except Distribution.DoesNotExist:
        raise Http404

    # Get unique gene ids
    gene_ids = distribution.gene_ids()
    title = "%s Parts" % distribution.name

    # then get parts
    queryset = Part.objects.filter(gene_id__in=gene_ids).order_by('gene_id')
    return catalog_pagination(request, queryset, "parts", title=title)


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def samples_catalog_view(request):
    queryset = Sample.objects.all().order_by('-time_updated')
    return catalog_pagination(request, queryset, "samples")

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def parts_catalog_view(request):
    queryset = Part.objects.all().order_by('-time_updated')
    return catalog_pagination(request, queryset, "parts")

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def plates_catalog_view(request):
    queryset = Plate.objects.all().order_by('-time_updated')
    return catalog_pagination(request, queryset, "plates")
