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
from django.shortcuts import render, get_object_or_404
from django.views.generic import View
from django.shortcuts import redirect

from fg.apps.factory.twist import (
    get_orders,
    get_client
)
from ratelimit.decorators import ratelimit
from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def twist_orders(request):
    '''Show a table of twist orders for the user.
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    # Returns empty list if no orders, or no credentials
    orders = get_orders()

    context = {"orders": orders}
    return render(request, 'twist/orders.html', context)


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def twist_order(request, uuid):
    '''Show a single twist order based on its unique id, the sfsc_id
    '''
    if not request.user.is_staff or not request.user.is_superuser:
        messages.info(request, "You are not allowed to see this view.")
        return redirect('dashboard')

    # Returns empty list if no orders, or no credentials
    items = []
    client = get_client()
    if client:
        items = client.order_items(uuid)

    context = {"items": items}
    return render(request, 'twist/order.html', context)
