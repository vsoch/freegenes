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
from fg.apps.orders.forms import (
    CheckoutForm,
    MTAForm
)

from fg.apps.orders.models import (
    Order, 
    Address
) 
from fg.apps.main.models import Distribution
from ratelimit.decorators import ratelimit
from fg.apps.orders.email import send_email
from fg.settings import (
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block,
    DOMAIN_NAME,
    HELP_CONTACT_EMAIL,
    NODE_NAME
)


@login_required
@ratelimit(key='ip', rate=rl_rate, block=rl_block)
def order_details(request, uuid):
    '''show details for an order. For an admin, this means we also allow to
       download or upload MTA for further processing. A user is only allowed
       to see orders that he/she owns.
    '''
    try:
        order = Order.objects.get(uuid=uuid)
    except Order.DoesNotExist:
        raise Http404

    if order.user == request.user or request.user.is_superuser:   
        return render(request, "details/order_details.html", context={'instance': order})

    messages.warning(request, "You don't have permission to see this view.")
    return redirect('catalog_view')


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

            # Remove the cart order if it's empty, they can re-generate
            if order.distributions.count() == 0:
                order.delete()
        else:
            messages.info(request, "This distribution was not in your cart.")
        return redirect('orders')

    else:
        messages.info(request, "You do not have an items in your cart.")
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

    # A cart exists, meaning an order that has status = Cart
    if order:

        # We only need to check to alert the user.
        if order.distributions.filter(uuid=distribution.uuid).exists():
            messages.info(request, "This distribution is already in your cart.")
        else:
            order.distributions.add(distribution)
            messages.info(request, "This distribution was added to your cart.")
        return redirect('orders')

    else:
        # We name the order based on the distribution added, must be cart
        order = Order.objects.create(user=request.user,
                                     status="Cart",
                                     name=distribution.name)
        order.distributions.add(distribution)
        order.save()
        messages.info(request, "This item was added to your cart.")
        return redirect('orders')


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

    # The order must be a cart (not already ordered)
    if order.status != "Cart":
        return JsonResponse({"message": "The order has already been submit",
                             "code": "error"})

    if request.user != order.user:
        return JsonResponse({"message": "You are not allowed to perform this action",
                             "code": "error"})

    # When the user submits, it's no longer a Cart, but Awaiting countersign
    # We can only get here when the user has uploaded the MTA
    order.status = 'Awaiting Countersign'
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
        context['orders'] = Order.objects.filter(user=request.user).exclude(status="Cart")
    return render(request, 'orders/orders.html', context)


class CheckoutView(View):
    '''Checkout a cart, meaning finishing up an order and placing it. We check
       for the MTA, along with ensuring that the order exists, period.
    '''

    @ratelimit(key='ip', rate=rl_rate, block=rl_block, method="GET")
    def get(self, *args, **kwargs):

        try:
            order = Order.objects.get(user=self.request.user, status="Cart")
            
            # redirect the user to the view to upload their own MTA.
            if order.material_transfer_agreement is None:
                messages.info(self.request, "You haven't signed an MTA yet for this order.")
                context = {"form": MTAForm(), 'order': order}
                return render(self.request, "orders/sign-mta.html", context)

            form = CheckoutForm()
            context = {
                'form': form,
                'order': order
            }
            return render(self.request, "orders/checkout.html", context)
        except Order.DoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect('orders')


    @ratelimit(key='ip', rate=rl_rate, block=rl_block, method="POST")
    def post(self, *args, **kwargs):
        '''When the user checks out, we validate the form data, add 
           it to the order, and then send an email to the lab to 
           link to further process the shipment.
        '''
        form = CheckoutForm(self.request.POST or None)

        try:
            order = Order.objects.get(uuid=kwargs.get('uuid'))
            if form.is_valid():

                # Get cleaned form data
                data = form.cleaned_data

                # First create the lab address, this data is always required
                lab_address = Address.objects.create(institution_name=data.get('lab_name', None),
                                                     recipient_title=data.get('recipient_title', None),
                                                     recipient_name=data.get('recipient_name', None),
                                                     address1=data.get('lab_address'),
                                                     address2=data.get('lab_address2', None),
                                                     postal_code=data.get('lab_zip'),
                                                     city=data.get('lab_city'),
                                                     state=data.get('lab_state'),
                                                     phone=data.get('lab_phone'),
                                                     country=data.get('lab_country'),
                                                     email=data.get('lab_email', None))

                # The user can request to use the same address for shipping
                if data.get('same_shipping_address', False) == True:
                    shipping_address = lab_address
                else:
                    shipping_address = Address.objects.create(recipient_name=data.get('shipping_to'),
                                                              address1=data.get('shipping_address'),
                                                              address2=data.get('shipping_address2', None),
                                                              postal_code=data.get('shipping_zip'),
                                                              phone=data.get('shipping_phone'),
                                                              city=data.get('shipping_city'),
                                                              state=data.get('shipping_state'),
                                                              country=data.get('shipping_country'),
                                                              email=data.get('lab_email', None))
 
                # When the order is checked out, update status to awaiting countersign
                order.status = "Awaiting Countersign"
                order.lab_address = lab_address
                order.shipping_address = shipping_address
                order.save()

                # Send email to lab with link to order
                comments = (self.request.POST.get('lab_comments', '') + 
                            self.request.POST.get('shipping_comments', ''))
                send_order_notification(order, comments=comments)

                messages.info(self.request, "Thank you for submitting your order!")
                return redirect("dashboard")

            # The form isn't valid
            context = {
                'form': form,
                'order': order
            }
            return render(self.request, "orders/checkout.html", context)

        except Order.DoesNotExist:                
            message.error(self.request, 'That order does not exist.')
            return redirect('orders')


def send_order_notification(order, comments):
    '''based on a submit order, send a notification, including a link to
       it's page to create a shipment. This relies on using the SendGrid API.
    '''
    print(comments)
    # Derive the message - it should include a link to the order, and comments
    link = "%s/%s" %(DOMAIN_NAME, order.get_absolute_url())
    subject = "New Order for %s: %s" % (NODE_NAME, order.name)
    message = "Woohoo! We have a new order!<br>%s<br>Comments:%s" %(link, comments)
    send_email(email_to=HELP_CONTACT_EMAIL, message=message, subject=subject)
