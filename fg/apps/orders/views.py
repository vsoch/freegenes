'''

Copyright (C) 2019 Vanessa Sochat.

This Source Code Form is subject to the terms of the
Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

'''

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import (
    Http404, 
    HttpResponseRedirect, 
    JsonResponse
)
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from fg.apps.orders.forms import (
    CheckoutForm,
    MTAForm
)

from fg.apps.orders.models import Order
from fg.apps.main.models import Distribution

from ratelimit.decorators import ratelimit
from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

import random
import string

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def order_details(request, uuid):

    try:
        order = Order.objects.get(uuid=uuid)
    except Order.DoesNotExist:
        raise Http404

    if order.user == request.user or request.user.is_superuser:   
        return render(request, "details/order_details.html", context={'instance': order})

    messages.warning(request, "You don't have permission to see this view.")
    redirect('catalog_view')


# Cart Operations

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def remove_from_cart(request, uuid):
    '''remove a distribution from the cart based on its uuid.
    '''
    distribution = get_object_or_404(Distribution, uuid=uuid)
    order = request.user.get_cart()

    if order:        
        if order.distributions.filter(uuid=distribution.uuid).exists():
            order.distributions.remove(distribution)
            messages.info(request, "This distribution was removed from your cart.")
        else:
            messages.info(request, "This distribution was not in your cart.")
        return redirect('orders')

    else:
        messages.info(request, "You do not have an active order.")
        return redirect("catalog_view")


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def add_to_cart(request, uuid):
    '''add a distribution id to the cart. if the user already has added it to
       an order not submit (representing an open cart) tell them. If the 
       distribution hasn't been added, add it.
    '''
    distribution = get_object_or_404(Distribution, uuid=uuid)
    order = request.user.get_cart()

    # A cart exists, meaning an order that has ordered=False
    if order:

        # We only need to check to alert the user.
        if order.distributions.filter(uuid=distribution.uuid).exists():
            messages.info(request, "This distribution is already in your cart.")
        else:
            order.distributions.add(distribution)
            messages.info(request, "This distribution was added to your cart.")
        return redirect('orders')

    else:
        # We name the order based on the distribution added
        order = Order.objects.create(user=request.user, name=distribution.name)
        order.distributions.add(distribution)
        order.save()
        messages.info(request, "This item was added to your cart.")
        return redirect('orders')

# Upload MTA

@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def upload_mta(request, uuid):
    '''a specific view to handle uploading the MTA form, redirected from the
       view to checkout in the case that an order is missing an MTA. The
       uuid corresponds to the UUID for the order
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
            print('FORM IS VALID')
            mta = form.save()
            order.material_transfer_agreement = mta
            order.save()
            return HttpResponseRedirect('checkout')
    else:
        form = MTAForm()
    context = {'form': form, 'order': order}
    return render(request, 'orders/sign-mta.html', context)


# Order Operations


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def submit_order(request, uuid):
    '''Submit an order, must be done by the owner
    '''
    try:
        order = Order.objects.get(uuid=uuid)
    except Order.DoesNotExist:
        return JsonResponse({"message": "The order does not exist.",
                             "code": "error"})

    # Was the order already ordered?
    if order.ordered:
        return JsonResponse({"message": "The order has already been submit",
                             "code": "error"})

    if request.user != order.user:
        return JsonResponse({"message": "You are not allowed to perform this action",
                             "code": "error"})

    order.ordered = True
    order.save()   
    return JsonResponse({"message": "Your order has been submit.",
                         "code": "success"})


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def orders_view(request):
    '''Show a table of orders for a user, if they are logged in.
    '''
    context = {}
    if request.user.is_authenticated:
        context['cart'] = request.user.get_cart()
        context['orders'] = Order.objects.filter(user=request.user, ordered=True)
    return render(request, 'orders/orders.html', context)


class CheckoutView(View):
    '''Checkout a cart, meaning finishing up an order and placing it. We check
       for the MTA, along with ensuring that the order exists, period.
    '''

    @ratelimit(key='ip', rate=rl_rate, block=rl_block, method="GET")
    def get(self, *args, **kwargs):

        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            
            # NOTE: this will redirect the user to the view to upload their own MTA.
            # This is currently disabled in favor of sending an email to the lab
            # and having the lab process the order and handle the MTA offline.
            # When this changes, this can be uncommented. The checkout view will 
            # also need to be changed to submit to server, and not to email.
            #if order.material_transfer_agreement is None:
            #    messages.info(self.request, "You haven't signed an MTA yet for this order.")
            #    context = {"form": MTAForm(), 'order': order}
            #    return render(self.request, "orders/sign-mta.html", context)

            form = CheckoutForm()
            context = {
                'form': form,
                'order': order
            }
            return render(self.request, "orders/checkout.html", context)
        except Order.DoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return render(self.request, "orders/checkout.html", context)

    @ratelimit(key='ip', rate=rl_rate, block=rl_block, method="POST")
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        print('TODO WRITE ME VANESSASAURUS')
