'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

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
    Tag
)

from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)


@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def index_view(request):
    return render(request, 'main/index.html')

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def about_view(request):
    return render(request, 'main/about.html')

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def terms_view(request):
    return render(request, 'terms/usage_agreement_fullwidth.html')

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def privacy_view(request):
    return render(request, 'terms/privacy_agreement.html')

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def dashboard_view(request):
    '''Show the logged in regular user their orders, or an admin/staff
       all orders. Also show stats for the node, not including Schema.
    '''
    context = {}

    # Counts go into the bar chart, should be scaled similarity
    context['counts'] = {
        "authors": Author.objects.count(),
        "containers": Container.objects.count(),
        "collections": Collection.objects.count(),
        "distributions": Distribution.objects.count(),
        "institutions": Institution.objects.count(),
        "modules": Module.objects.count(),
        "operations": Operation.objects.count(),
        "organisms": Organism.objects.count(),
        "plans": Plan.objects.count(),
        "platesets": PlateSet.objects.count(),
        "robots": Robot.objects.count(),
        "protocols": Protocol.objects.count()
    }

    # These are printed (numbers) since they are larged
    context['parts_count'] = Part.objects.count()
    context['samples_count'] = Sample.objects.count()
    context['plates_count'] = Plate.objects.count()
    context['tags_count'] = Tag.objects.count()

    orders = []
    if request.user.is_superuser or request.user.is_staff:
        orders = Order.objects.all()
    elif request.user.is_authenticated:
        orders = Order.objects.filter(user=request.user)

    context['orders'] = orders
    return render(request, 'main/dashboard.html', context)

@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def contact_view(request):
    return render(request, 'main/contact.html')
