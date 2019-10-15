'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    Http404, 
    JsonResponse
)
from django.shortcuts import render
from django.shortcuts import redirect
from fg.apps.factory.models import FactoryOrder

from ratelimit.decorators import ratelimit
from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def factory_view(request):
    '''Show different factory operations to the user, including importing
       and managing orders from twist
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    orders = FactoryOrder.objects.all()
    return render(request, 'factory/incoming.html', {"orders": orders})


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def view_factoryorder_parts(request, uuid):
    '''Given a unique ID for a factory order, show a table of parts 
       associated. This view is linked from the main factory page.
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    try:
        order = FactoryOrder.objects.get(uuid=uuid)
    except FactoryOrder.DoesNotExist:
        messages.info(request, "This factory order does not exist.")
        return redirect('factory')

    return render(request, 'tables/twist_parts.html', {"order": order})
