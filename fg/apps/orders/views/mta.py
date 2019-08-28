'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from fg.apps.orders.forms import MTAForm
from fg.apps.orders.models import Order

from ratelimit.decorators import ratelimit
from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

def _upload_mta(request, uuid, template="orders/sign-mta.html"):
    '''a general view to handle uploading the MTA form, is used for both the
       admin and user upload forms, but each return different templates.
    '''
    # The order must exist, we look up based on uuid
    try:
        order = Order.objects.get(uuid=uuid)
    except Order.DoesNotExist:
        messages.info(request, "We can't find an order with that identifier.")
        return redirect('orders')        

    if request.method == 'POST':
        form = MTAForm(request.POST, request.FILES)

        # If the form is valid, save to the order and continue checkout
        if form.is_valid():
            mta = form.save()
            order.material_transfer_agreement = mta
            order.save()
            return redirect('checkout')
    else:
        form = MTAForm()
    context = {'form': form, 'order': order}
    return render(request, template, context)


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def upload_mta(request, uuid):
    '''a specific view to handle uploading the MTA form, redirected from the
       view to checkout in the case that an order is missing an MTA. The
       uuid corresponds to the UUID for the order
    '''
    return _upload_mta(request, uuid)


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def admin_upload_mta(request, uuid):
    '''the admin view to upload the MTA - the same variables and functionality,
       but a different template.
    '''
    if request.user.is_staff or request.user.is_superuser:
        return _upload_mta(request, uuid, template='orders/upload-mta.html')
    messages.warning(request, 'You are not allowed to perform this action.')
    redirect('orders')
