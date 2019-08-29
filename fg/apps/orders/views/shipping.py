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
from django.shortcuts import render, redirect
from django.views.generic import View
from fg.apps.orders.forms import (
    ShippingForm
)

from fg.apps.orders.models import Order
from ratelimit.decorators import ratelimit
from fg.settings import (
    NODE_INSTITUTION,
    HELP_CONTACT_EMAIL,
    SHIPPO_TOKEN,
    VIEW_RATE_LIMIT as rl_rate, 
    VIEW_RATE_LIMIT_BLOCK as rl_block
)

import shippo

# Default parcel dimensions

parcel_default = {
    "length": "5",
    "width": "5",
    "height": "5",
    "distance_unit": "in",
    "weight": "2",
    "mass_unit": "lb"
}


class ShippingView(View):
    '''Checkout a cart, meaning finishing up an order and placing it. We check
       for the MTA, along with ensuring that the order exists, period.
    '''

    @ratelimit(key='ip', rate=rl_rate, block=rl_block, method="GET")
    def get(self, *args, **kwargs):
        '''create a shipment for a given order
        '''
        if not self.request.user.is_staff or self.request.user.is_superuser:
            messages.warning(self.request, "You don't have permission to see this view.")
            redirect('catalog_view')

        try:
           # An order cannot be already processed (received is True)
           order = Order.objects.get(uuid=kwargs.get('uuid'), received=False)
        except Order.DoesNotExist:
            raise Http404

        # If no MTA, redirect back to the order page with instructions to get it
        if not order.material_transfer_agreement:
            messages.warning(self.request, "This order needs an MTA before proceeding.")
            redirect('order_details', args=(order.uuid,))
            
        form = ShippingForm()
        context = {
            'form': form,
            'order': order
        }
        return render(self.request, "shipping/create.html", context)

    @ratelimit(key='ip', rate=rl_rate, block=rl_block, method="POST")
    def post(self, *args, **kwargs):
        '''This can be written if form data is ever sent to the server
        '''
        form = ShippingForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, received=False)
            if form.is_valid():

                # Get cleaned form data
                data = form.cleaned_data
                data['shipping_email'] = request.user.email
                addresses = create_addresses(data)    

                # Ensure that both addresses are valid
                for address_type, address_data in addresses.items():
                    if not address_data['validation_results']['is_valid']:
                        messages = "<br>".join(address_data['validation_results']['messages'])
                        messages.error(self.request, '%s address is invalid. %s' %(address_type, address_data)) 
                        redirect('create_shipment', args=(order.uuid,))

                # Create the shipment, return to view
                shipment = create_shipment(addresses)
                context = {"shipment": shipment, "order": order}
                return render(self.request, "shipping/created.html", context)

        except Order.DoesNotExist:                
            message.error(self.request, 'That order does not exist.')
            redirect('orders')


# Helper Functions

def create_shipment(addresses, data):
    '''create a shipment using the default parcel dimensions, and the valid
       addresses. The SHIPPO_TOKEN and parcel_default should be import into
       the module. We take again the original input data to see if the user 
       wants dry ice.
    '''
    extra = {}

    # Does the shipment need dry ice?
    if data.get('dryice_options', 'No') == 'Yes':
        extra = {'dry_ice': {"contains_dry_ice": True, "weight": "2"}}

    return shippo.Shipment.create(
               address_from = addresses["From"],
               address_to = addresses["To"],
               parcels = [parcel_default],
               api_key = SHIPPO_TOKEN,
               extra = extra
    )

def create_addresses(data):
    '''create a shipment, where data is the cleaned data from the ShippingForm.
       If the shipment contains dry ice, the default weight is set to 2 (not
       sure what this means). We assume the country to be US.

       Parameters
       ==========
       data: the form.cleaned_data, expected to include:
	{'shipping_to': 'Mr. Bigglesworth',
	 'shipping_address': '2000 Campus Drive',
	 'shipping_zip': '94305',
	 'from_name': 'Dinosaur Labs',
	 'from_address': '2128 Roaring Ave Apt 410',
	 'from_zip': '12345',
	 'dryice_options': 'Yes'}
    '''
    # Create the address - it must be valid
    address_from = shippo.Address.create(
        name = data.get('from_name'),
        company = NODE_INSTITUTION,
        street1 = data.get('from_address'),
        street2 = data.get('from_address2'),
        zip = data.get('from_zip'),
        api_key=SHIPPO_TOKEN,
        country = "US", 
        email = HELP_CONTACT_EMAIL,
        validate = True
    )
        
    address_to = shippo.Address.create(
        name = data.get('shipping_to'),
        street1 = data.get('shipping_address'),
        street2 = data.get('shipping_address2'),
        zip = data.get('shipping_zip'),
        api_key=SHIPPO_TOKEN,
        country = "US", 
        email = data.get('shipping_email'),
        validate = True
    )

    return {'To': address_to,
            'From': address_from}
