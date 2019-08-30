'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.core.paginator import Paginator
from django.shortcuts import render 
from ratelimit.decorators import ratelimit

from fg.apps.main.models import (
    Collection,
    Distribution,
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
